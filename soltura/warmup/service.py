import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.language.nlp import analyze
from soltura.learner.models import KnowledgeType, MemoryCard, Rating, ReviewSource, WordContext
from soltura.learner.repository import get_lexemes_by_ids
from soltura.llm.client import LLMClient, LLMUnavailableError
from soltura.practice.checking import (
    SPANISH_RATING,
    VERDICT_RATING,
    SpanishCheck,
    TranslationVerdict,
    check_spanish,
    judge_translation,
)
from soltura.srs.service import due_queue, review

logger = logging.getLogger(__name__)

WARMUP_SIZE = 15

CONTEXT_SYSTEM = (
    "You write one short, natural Spanish sentence from everyday life in Spain, at CEFR level "
    "A2, for a vocabulary review card. The sentence must use the given word, in any form that "
    "fits, and must differ from the sentences the learner has already seen. Give the exact form "
    "of the word as it appears in your sentence, and a natural Ukrainian translation of the "
    "whole sentence."
)


class ContextSentence(BaseModel):
    sentence: str = Field(description="The new Spanish sentence")
    target_form: str = Field(description="The word exactly as it appears in the sentence")
    translation: str = Field(description="Ukrainian translation of the whole sentence")


class WarmupItem(BaseModel):
    card_id: int = Field(description="Card being reviewed")
    knowledge_type: KnowledgeType = Field(description="Recognize or recall")
    lemma: str = Field(description="Dictionary form of the word")
    sentence: str = Field(description="Spanish sentence the word is shown in")
    target_form: str = Field(description="The word exactly as it appears in the sentence")
    translation: str | None = Field(
        default=None, description="Ukrainian translation of the sentence; recall cards need it"
    )


@dataclass(frozen=True)
class AnswerResult:
    rating: Rating
    expected: str
    explanation: str


def _find_form(sentence: str, form: str) -> bool:
    return form.lower() in sentence.lower()


def _form_in_saved_sentence(sentence: str, lemma: str) -> str | None:
    for token in analyze(sentence):
        if token.lemma == lemma:
            return token.text
    return lemma if _find_form(sentence, lemma) else None


async def _fresh_context(llm: LLMClient, lemma: str, seen: list[str]) -> ContextSentence | None:
    seen_block = "\n".join(f"- {sentence}" for sentence in seen) or "- (none)"
    try:
        context = await llm(
            ContextSentence,
            system=CONTEXT_SYSTEM,
            prompt=f"Word: {lemma}\nSentences already seen:\n{seen_block}",
            effort="low",
            max_tokens=4_000,
        )
    except LLMUnavailableError as error:
        logger.warning(f"Context generation failed for {lemma!r}: {error}")
        return None
    if not _find_form(context.sentence, context.target_form) or context.sentence in seen:
        logger.debug(f"Discarded generated context for {lemma!r}: {context.sentence!r}")
        return None
    return context


async def build_warmup(
    session: AsyncSession, llm: LLMClient, learner_id: int, now: datetime
) -> list[WarmupItem]:
    cards = await due_queue(session, learner_id, now=now, limit=WARMUP_SIZE)
    if not cards:
        return []
    lemmas = {
        lexeme.id: lexeme.lemma
        for lexeme in await get_lexemes_by_ids(session, {card.lexeme_id for card in cards})
    }
    saved = await session.execute(
        select(WordContext.lexeme_id, WordContext.sentence)
        .where(
            col(WordContext.learner_id) == learner_id,
            col(WordContext.lexeme_id).in_(lemmas),
        )
        .order_by(col(WordContext.created_at))
    )
    seen: dict[int, list[str]] = {}
    for lexeme_id, sentence in saved.all():
        seen.setdefault(lexeme_id, []).append(sentence)

    # One concurrent batch: a warm-up of 15 cards should not wait for 15 calls in a row.
    contexts = await asyncio.gather(
        *(
            _fresh_context(llm, lemmas[card.lexeme_id], seen.get(card.lexeme_id, []))
            for card in cards
        )
    )

    items: list[WarmupItem] = []
    for card, context in zip(cards, contexts, strict=True):
        if card.id is None:
            continue
        lemma = lemmas[card.lexeme_id]
        if context is not None:
            items.append(
                WarmupItem(
                    card_id=card.id,
                    knowledge_type=card.knowledge_type,
                    lemma=lemma,
                    sentence=context.sentence,
                    target_form=context.target_form,
                    translation=context.translation,
                )
            )
            continue
        # Without a fresh sentence a recall card has no Ukrainian prompt to answer, so
        # it waits for the next warm-up; recognize falls back to the saved sentence.
        fallback = seen.get(card.lexeme_id, [])
        form = _form_in_saved_sentence(fallback[-1], lemma) if fallback else None
        if card.knowledge_type == KnowledgeType.RECOGNIZE and fallback and form:
            items.append(
                WarmupItem(
                    card_id=card.id,
                    knowledge_type=card.knowledge_type,
                    lemma=lemma,
                    sentence=fallback[-1],
                    target_form=form,
                )
            )
    return recall_before_recognize(items)


def recall_before_recognize(items: list[WarmupItem]) -> list[WarmupItem]:
    # A recognize card shows the word, which would give away the answer to the same
    # word's recall card later in the warm-up; the pair swaps slots, so the queue's
    # spacing between them stays as it was.
    ordered = list(items)
    for i, item in enumerate(ordered):
        if item.knowledge_type != KnowledgeType.RECOGNIZE:
            continue
        for j in range(i + 1, len(ordered)):
            later = ordered[j]
            if later.lemma == item.lemma and later.knowledge_type == KnowledgeType.RECALL:
                ordered[i], ordered[j] = later, item
                break
    return ordered


async def answer_item(
    session: AsyncSession,
    llm: LLMClient,
    learner_id: int,
    item: WarmupItem,
    answer: str,
    duration_ms: int | None,
    now: datetime,
) -> AnswerResult:
    card = await session.get(MemoryCard, item.card_id)
    if card is None or card.learner_id != learner_id:
        raise PermissionError("This card does not belong to the learner")

    if item.knowledge_type == KnowledgeType.RECALL:
        check = check_spanish(answer, item.target_form, item.lemma)
        rating = SPANISH_RATING[check]
        result = AnswerResult(
            rating=rating, expected=item.target_form, explanation=_spanish_explanation(check, item)
        )
    else:
        verdict: TranslationVerdict = await judge_translation(
            llm, answer, item.target_form, item.sentence
        )
        rating = VERDICT_RATING[verdict.verdict]
        result = AnswerResult(rating=rating, expected=verdict.expected, explanation=verdict.reason)

    await review(
        session,
        card,
        rating,
        ReviewSource.WARMUP,
        now,
        answer=answer.strip() or None,
        duration_ms=duration_ms,
    )
    return result


def _spanish_explanation(check: SpanishCheck, item: WarmupItem) -> str:
    return {
        SpanishCheck.EXACT: "Правильно.",
        SpanishCheck.ACCENT_SLIP: f"Майже: перевірте наголос чи ñ — {item.target_form}.",
        SpanishCheck.TYPO: f"Майже: одна буква не та — {item.target_form}.",
        SpanishCheck.OTHER_FORM: f"Слово правильне, але тут потрібна форма {item.target_form}.",
        SpanishCheck.WRONG: f"Правильна відповідь: {item.target_form} ({item.lemma}).",
    }[check]
