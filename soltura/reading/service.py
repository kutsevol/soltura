import re
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.coverage import measure_coverage, words_to_replace
from soltura.language.nlp import analyze
from soltura.learner.models import (
    CefrLevel,
    KnowledgeType,
    Learner,
    LexemeStatus,
    MemoryCard,
    Rating,
    ReviewSource,
)
from soltura.learner.models import Lexeme as LexemeRow
from soltura.learner.repository import (
    get_due_card,
    get_learner_lemmas,
    get_lexemes_by_ids,
    get_lexemes_by_lemmas,
    get_most_frequent_lemmas,
)
from soltura.llm.client import LLMClient
from soltura.srs.service import due_queue, review, save_word

TARGET_COVERAGE = 0.95
MAX_SIMPLIFICATIONS = 2
# Until onboarding measures the learner, the most frequent lemmas stand in for what an
# A2 learner knows. wordfreq ranks web text, so everyday words like "cocina", "beber"
# or "cansado" sit between 1,500 and 3,000; at 1,500 live texts on family or sport
# came out at 83-88% and were stripped of exactly those words.
BASELINE_KNOWN_RANK = 3000
MAX_DUE_LEMMAS = 10
UNRANKED = 1_000_000

WRITER_SYSTEM = (
    "You write short Spanish reading texts for an adult Ukrainian speaker who lives in Spain "
    "and is learning Spanish. Write natural, everyday Spanish from Spain at the requested CEFR "
    "level: short sentences, frequent words, and the grammar a learner at that level has met. "
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


@dataclass(frozen=True)
class Segment:
    text: str
    is_word: bool


async def lemmas_counted_as_known(session: AsyncSession, learner_id: int) -> set[str]:
    # Words being learned count as known: texts include due words on purpose, and
    # treating them as unknown would make simplification strip them out again.
    known = await get_learner_lemmas(session, learner_id, [LexemeStatus.KNOWN])
    if not known:
        known = await get_most_frequent_lemmas(session, BASELINE_KNOWN_RANK)
    return known | await get_learner_lemmas(session, learner_id, [LexemeStatus.LEARNING])


async def due_lemmas(session: AsyncSession, learner_id: int, now: datetime) -> list[str]:
    cards = await due_queue(session, learner_id, now=now, limit=MAX_DUE_LEMMAS * 2)
    lexeme_ids = list(dict.fromkeys(card.lexeme_id for card in cards))[:MAX_DUE_LEMMAS]
    by_id = {lexeme.id: lexeme.lemma for lexeme in await get_lexemes_by_ids(session, lexeme_ids)}
    return [by_id[lexeme_id] for lexeme_id in lexeme_ids if lexeme_id in by_id]


def _level(learner: Learner) -> str:
    return (learner.reading_level or CefrLevel.A2).value.upper()


def _first_draft_prompt(level: str, topic: str, due: list[str], source_text: str | None) -> str:
    wanted = (
        f" Where it fits naturally, use these words the learner is reviewing: {', '.join(due)}."
        if due
        else ""
    )
    if source_text is not None:
        return (
            f"Rewrite the text below for CEFR level {level}, keeping its meaning and facts. "
            f"About 120 to 200 words.{wanted}\n\n<source>\n{source_text}\n</source>"
        )
    return f"CEFR level {level}. Topic: {topic}. About 120 to 180 words.{wanted}"


def _simplify_prompt(level: str, draft: GeneratedText, rare: list[str], due: list[str]) -> str:
    keep = f" Keep these words, the learner is reviewing them: {', '.join(due)}." if due else ""
    return (
        f"A few words in this text are too rare for CEFR level {level}: {', '.join(rare)}. "
        "Replace each with a simpler word that means the same, or rewrite its sentence without "
        "it. Never describe a word with a roundabout phrase ('el hijo de mi hijo' for 'nieto'): "
        f"if no simple word fits, keep the original. Change nothing else.{keep}"
        f"\n\n<title>{draft.title}</title>\n<text>\n{draft.text}\n</text>"
    )


async def prepare_text(
    session: AsyncSession,
    llm: LLMClient,
    learner: Learner,
    now: datetime,
    topic: str,
    source_text: str | None = None,
) -> PreparedText:
    if learner.id is None:
        raise ValueError("The learner must be saved before a text is prepared")
    level = _level(learner)
    known = await lemmas_counted_as_known(session, learner.id)
    due = await due_lemmas(session, learner.id, now)

    draft = await llm(
        GeneratedText,
        system=WRITER_SYSTEM,
        prompt=_first_draft_prompt(level, topic, due, source_text),
        effort="medium",
    )
    attempts = 1
    coverage = measure_coverage(analyze(f"{draft.title}. {draft.text}"), known)
    while coverage.ratio < TARGET_COVERAGE and attempts <= MAX_SIMPLIFICATIONS:
        ranks = {
            lexeme.lemma: lexeme.frequency_rank
            for lexeme in await get_lexemes_by_lemmas(session, coverage.unknown_lemmas)
        }
        rare = words_to_replace(coverage, ranks, TARGET_COVERAGE)
        draft = await llm(
            GeneratedText,
            system=WRITER_SYSTEM,
            prompt=_simplify_prompt(level, draft, rare, due),
            effort="medium",
        )
        attempts += 1
        coverage = measure_coverage(analyze(f"{draft.title}. {draft.text}"), known)

    return PreparedText(
        title=draft.title,
        text=draft.text,
        coverage=coverage.ratio,
        attempts=attempts,
        below_target=coverage.ratio < TARGET_COVERAGE,
        unknown_lemmas=coverage.unknown_lemmas,
    )


async def tap_word(
    session: AsyncSession,
    llm: LLMClient,
    learner_id: int,
    word: str,
    sentence: str,
    now: datetime,
) -> TapResult:
    gloss = await llm(
        Gloss,
        system=GLOSS_SYSTEM,
        prompt=f"Word: {word}\nSentence: {sentence}",
        effort="low",
        max_tokens=4_000,
    )
    lemma = gloss.lemma.strip().lower()
    reviewed = False
    lexemes = await get_lexemes_by_lemmas(session, [lemma])
    if lexemes and lexemes[0].id is not None:
        # Looking a due word up is a failed recognition, the only signal reading gives.
        card = await get_due_card(session, learner_id, lexemes[0].id, KnowledgeType.RECOGNIZE, now)
        if card is not None:
            await review(session, card, Rating.AGAIN, ReviewSource.READING_TAP, now)
            reviewed = True
    return TapResult(word=word, lemma=lemma, translation=gloss.translation, reviewed=reviewed)


async def save_tapped_word(
    session: AsyncSession,
    learner_id: int,
    lemma: str,
    sentence: str,
    now: datetime,
    topic: str | None = None,
) -> list[MemoryCard]:
    lemma = lemma.strip().lower()
    # The LLM's lemma can be one the frequency seed never ranked; it still gets a
    # lexeme, at the bottom of the frequency order, so the word can be learned.
    await session.execute(
        insert(LexemeRow)
        .values(lemma=lemma, pos="X", frequency_rank=UNRANKED)
        .on_conflict_do_nothing(index_elements=["lemma"])
    )
    [lexeme] = await get_lexemes_by_lemmas(session, [lemma])
    if lexeme.id is None:
        raise ValueError(f"Lexeme for {lemma!r} has no id")
    return await save_word(session, learner_id, lexeme.id, sentence, now, topic)


_SENTENCE = re.compile(r"[^.!?…]+(?:[.!?…]+|$)\s*")
_WORD = re.compile(r"[^\W\d_]+|[\W\d_]+")


def split_for_reading(text: str) -> list[list[list[Segment]]]:
    # paragraphs -> sentences -> segments, so the page can send a tapped word
    # together with the sentence it appears in.
    return [
        [
            [Segment(text=part, is_word=part[0].isalpha()) for part in _WORD.findall(sentence)]
            for sentence in _SENTENCE.findall(paragraph.strip())
            if sentence.strip()
        ]
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]
