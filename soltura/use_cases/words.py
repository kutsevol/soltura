from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.repository import SavedWord, get_saved_words
from soltura.llm.client import LLMClient
from soltura.use_cases.reading import save_tapped_word
from soltura.words.service import (
    MAX_LEMMA_LENGTH,
    MAX_SENTENCE_LENGTH,
    MAX_WORDS,
    InvalidAddForm,
    InvalidLookup,
    LineResult,
    LookupProblem,
    look_up_words,
    parse_words,
)
from soltura.words.vocabulary import VocabularyMap, build_vocabulary_map


async def look_up_text(
    session: AsyncSession, llm: LLMClient, learner_id: int, text: str
) -> list[LineResult]:
    lines = parse_words(text)
    if not lines:
        raise InvalidLookup(LookupProblem.EMPTY)
    if len(lines) > MAX_WORDS:
        raise InvalidLookup(LookupProblem.TOO_MANY)
    return await look_up_words(session, llm, learner_id, lines)


async def add_words(
    session: AsyncSession,
    learner_id: int,
    lemmas: list[str],
    sentences: list[str],
    now: datetime,
) -> list[str]:
    pairs = list(zip(lemmas, sentences, strict=False))
    if (
        not 0 < len(lemmas) <= MAX_WORDS
        or len(lemmas) != len(sentences)
        or any(not 0 < len(lemma.strip()) <= MAX_LEMMA_LENGTH for lemma, _ in pairs)
        or any(not 0 < len(sentence.strip()) <= MAX_SENTENCE_LENGTH for _, sentence in pairs)
    ):
        raise InvalidAddForm
    for lemma, sentence in pairs:
        await save_tapped_word(session, learner_id, lemma, sentence, now)
    return [lemma.strip().lower() for lemma in lemmas]


async def find_saved_words(session: AsyncSession, learner_id: int, search: str) -> list[SavedWord]:
    return await get_saved_words(session, learner_id, search.strip())


async def vocabulary_map(session: AsyncSession, learner_id: int) -> VocabularyMap:
    return await build_vocabulary_map(session, learner_id)
