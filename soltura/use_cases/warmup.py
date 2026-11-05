import asyncio
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.learner.models import (
    KnowledgeType,
    MemoryCard,
    ReviewSource,
    UnitKind,
    WordContext,
)
from soltura.learner.repository import get_lexemes_by_ids
from soltura.llm.client import LLMClient
from soltura.practice.checking import (
    SPANISH_RATING,
    VERDICT_RATING,
    TranslationVerdict,
    check_spanish,
    judge_translation,
)
from soltura.srs.service import due_queue, review
from soltura.warmup.service import (
    WARMUP_SIZE,
    AnswerResult,
    WarmupItem,
    form_in_saved_sentence,
    fresh_context,
    recall_before_recognize,
    spanish_explanation,
)


async def build_warmup(
    session: AsyncSession, llm: LLMClient, learner_id: int, now: datetime
) -> list[WarmupItem]:
    queue = await due_queue(
        session, learner_id, now=now, limit=WARMUP_SIZE, unit_kind=UnitKind.WORD
    )
    cards = [(card, card.lexeme_id) for card in queue if card.lexeme_id is not None]
    if not cards:
        return []
    lemmas = {
        lexeme.id: lexeme.lemma
        for lexeme in await get_lexemes_by_ids(session, {lexeme_id for _, lexeme_id in cards})
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
        *(fresh_context(llm, lemmas[lexeme_id], seen.get(lexeme_id, [])) for _, lexeme_id in cards)
    )

    items: list[WarmupItem] = []
    for (card, lexeme_id), context in zip(cards, contexts, strict=True):
        if card.id is None:
            continue
        lemma = lemmas[lexeme_id]
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
        fallback = seen.get(lexeme_id, [])
        form = form_in_saved_sentence(fallback[-1], lemma) if fallback else None
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
            rating=rating, expected=item.target_form, explanation=spanish_explanation(check, item)
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
