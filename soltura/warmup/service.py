import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field

from soltura.language.nlp import analyze
from soltura.language.range import knows_sentence
from soltura.learner.models import (
    KnowledgeType,
    Rating,
)
from soltura.llm.client import LLMClient, LLMUnavailableError
from soltura.practice.checking import (
    SpanishCheck,
)
from soltura.practice.text import split_around

logger = logging.getLogger(__name__)

WARMUP_SIZE = 15

CONTEXT_SYSTEM = (
    "You write one short, natural Spanish sentence from everyday life in Spain for a "
    "vocabulary review card. You are told how many of the most frequent Spanish words the "
    "learner knows: build the sentence from those words, apart from the given word. The "
    "sentence must use the given word, in any form that fits, and must differ from the "
    "sentences the learner has already seen. Give the exact form of the word as it appears in "
    "your sentence, and a natural Ukrainian translation of the whole sentence."
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
    return split_around(sentence, form) is not None


def form_in_saved_sentence(sentence: str, lemma: str) -> str | None:
    for token in analyze(sentence):
        if token.lemma == lemma:
            return token.text
    return lemma if _find_form(sentence, lemma) else None


async def fresh_context(
    llm: LLMClient, lemma: str, seen: list[str], vocabulary: int
) -> ContextSentence | None:
    seen_block = "\n".join(f"- {sentence}" for sentence in seen) or "- (none)"
    try:
        context = await llm(
            ContextSentence,
            system=CONTEXT_SYSTEM,
            prompt=(
                f"{knows_sentence(vocabulary)}\nWord: {lemma}\n"
                f"Sentences already seen:\n{seen_block}"
            ),
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


def spanish_explanation(check: SpanishCheck, item: WarmupItem) -> str:
    return {
        SpanishCheck.EXACT: "Правильно.",
        SpanishCheck.ACCENT_SLIP: f"Майже: перевірте наголос чи ñ — {item.target_form}.",
        SpanishCheck.TYPO: f"Майже: одна буква не та — {item.target_form}.",
        SpanishCheck.OTHER_FORM: f"Слово правильне, але тут потрібна форма {item.target_form}.",
        SpanishCheck.WRONG: f"Правильна відповідь: {item.target_form} ({item.lemma}).",
    }[check]
