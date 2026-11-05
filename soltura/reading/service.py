from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.frequency import BANDS
from soltura.learner.models import (
    LexemeStatus,
    UnitKind,
)
from soltura.learner.repository import (
    get_latest_placement_run,
    get_learner_lemmas,
    get_lexemes_by_ids,
    get_most_frequent_lemmas,
)
from soltura.srs.service import due_queue

TARGET_COVERAGE = 0.95
MAX_SIMPLIFICATIONS = 2
# Until onboarding measures the learner, the most frequent lemmas stand in for what an
# A2 learner knows. wordfreq ranks web text, so everyday words like "cocina", "beber"
# or "cansado" sit between 1,500 and 3,000; at 1,500 live texts on family or sport
# came out at 83-88% and were stripped of exactly those words.
BASELINE_KNOWN_RANK = 3000
# A learner who passed no band of the placement test knows less than the first band.
FIRST_BAND_RANK = BANDS[0][1]
MAX_DUE_LEMMAS = 10
RECENT_TITLES = 5

WRITER_SYSTEM = (
    "You write short Spanish reading texts for an adult Ukrainian speaker who lives in Spain "
    "and is learning Spanish. Write natural, everyday Spanish from Spain within the vocabulary "
    "range you are told: short sentences, frequent words, and the grammar such a learner has met. "
    "Call things by their own word (nieto, bicicleta, traducir) rather than a roundabout "
    "phrase. Return only the title and the finished text: no translation, glossary, notes or "
    "corrections of yourself inside the text."
)

GLOSS_SYSTEM = (
    "You explain one Spanish word to a Ukrainian-speaking learner. Give the word's dictionary "
    "form (lemma) as it is used in the given sentence, so that 'fue' in 'Ayer fue al médico' is "
    "'ir' and in 'La película fue buena' is 'ser'. Give its meaning in this sentence in "
    "Ukrainian, in a few words."
)


class GeneratedText(BaseModel):
    title: str = Field(description="Short Spanish title of the text")
    text: str = Field(description="The Spanish text, paragraphs separated by blank lines")


class Gloss(BaseModel):
    lemma: str = Field(description="Dictionary form of the word as used in the sentence")
    translation: str = Field(description="Meaning of the word in this sentence, in Ukrainian")


@dataclass(frozen=True)
class PreparedText:
    title: str
    text: str
    coverage: float
    attempts: int
    below_target: bool
    unknown_lemmas: list[str]


@dataclass(frozen=True)
class TapResult:
    word: str
    lemma: str
    translation: str
    reviewed: bool


async def vocabulary_range(session: AsyncSession, learner_id: int) -> int:
    # The placement test is the only measure of the learner's vocabulary; without it the
    # baseline stands in. A run that passed no band still means "less than the baseline".
    run = await get_latest_placement_run(session, learner_id)
    if run is None:
        return BASELINE_KNOWN_RANK
    return max(run.known_rank, FIRST_BAND_RANK)


async def lemmas_counted_as_known(session: AsyncSession, learner_id: int) -> set[str]:
    # Words being learned count as known: texts include due words on purpose, and
    # treating them as unknown would make simplification strip them out again.
    known = await get_learner_lemmas(session, learner_id, [LexemeStatus.KNOWN])
    if not known:
        known = await get_most_frequent_lemmas(session, await vocabulary_range(session, learner_id))
    return known | await get_learner_lemmas(session, learner_id, [LexemeStatus.LEARNING])


async def due_lemmas(session: AsyncSession, learner_id: int, now: datetime) -> list[str]:
    cards = await due_queue(
        session, learner_id, now=now, limit=MAX_DUE_LEMMAS * 2, unit_kind=UnitKind.WORD
    )
    lexeme_ids = list(
        dict.fromkeys(card.lexeme_id for card in cards if card.lexeme_id is not None)
    )[:MAX_DUE_LEMMAS]
    by_id = {lexeme.id: lexeme.lemma for lexeme in await get_lexemes_by_ids(session, lexeme_ids)}
    return [by_id[lexeme_id] for lexeme_id in lexeme_ids if lexeme_id in by_id]


def _knows(vocabulary: int) -> str:
    return f"The learner knows about the {vocabulary:,} most frequent Spanish words."


def first_draft_prompt(
    vocabulary: int, topic: str, due: list[str], source_text: str | None, variation: str
) -> str:
    wanted = (
        f" Where it fits naturally, use these words the learner is reviewing: {', '.join(due)}."
        if due
        else ""
    )
    if source_text is not None:
        return (
            f"Rewrite the text below for a learner. {_knows(vocabulary)} Keep its meaning and "
            f"facts. About 120 to 200 words.{wanted}\n\n<source>\n{source_text}\n</source>"
        )
    return f"{_knows(vocabulary)} Topic: {topic}. About 120 to 180 words.{wanted}{variation}"


def simplify_prompt(vocabulary: int, draft: GeneratedText, rare: list[str], due: list[str]) -> str:
    keep = f" Keep these words, the learner is reviewing them: {', '.join(due)}." if due else ""
    return (
        f"{_knows(vocabulary)} A few words in this text are too rare for them: {', '.join(rare)}. "
        "Replace each with a simpler word that means the same, or rewrite its sentence without "
        "it. Never describe a word with a roundabout phrase ('el hijo de mi hijo' for 'nieto'): "
        f"if no simple word fits, keep the original. Change nothing else.{keep}"
        f"\n\n<title>{draft.title}</title>\n<text>\n{draft.text}\n</text>"
    )
