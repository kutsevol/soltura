from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from soltura.learner.models import Learner, MemoryCard
from soltura.srs.service import save_word
from soltura.use_cases.words import add_words, find_saved_words, look_up_text, vocabulary_map
from soltura.words.service import (
    MAX_LEMMA_LENGTH,
    MAX_SENTENCE_LENGTH,
    MAX_WORDS,
    InvalidAddForm,
    InvalidLookup,
    LookupProblem,
    WordEntry,
)
from tests.factories import LexemeFactory
from tests.fakes import FakeLLM

NIETO = WordEntry(
    is_spanish_word=True, lemma="nieto", translation="онук", sentence="Mi nieto juega en el parque."
)
SUEGRA = WordEntry(
    is_spanish_word=True,
    lemma="suegra",
    translation="свекруха",
    sentence="Mi suegra cocina muy bien.",
)
NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


async def _cards(session: AsyncSession) -> int:
    return (await session.execute(select(func.count()).select_from(MemoryCard))).scalar_one()


async def test_added_words_are_saved_with_two_cards_each_and_come_back_cleaned(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    lemmas = await add_words(
        session, learner.id, [" Nieto ", "suegra"], [NIETO.sentence, SUEGRA.sentence], NOW
    )

    assert lemmas == ["nieto", "suegra"]
    assert await _cards(session) == 4


@pytest.mark.parametrize(
    ("lemmas", "sentences"),
    [
        ([], []),
        (["nieto", "suegra"], ["Hola."]),
        (["  "], ["Hola."]),
        (["nieto"], ["  "]),
        (["x" * (MAX_LEMMA_LENGTH + 1)], ["Hola."]),
        (["nieto"], ["x" * (MAX_SENTENCE_LENGTH + 1)]),
        ([f"palabra{i}" for i in range(MAX_WORDS + 1)], ["Hola."] * (MAX_WORDS + 1)),
    ],
    ids=[
        "none",
        "unpaired",
        "blank-word",
        "blank-sentence",
        "long-word",
        "long-sentence",
        "too-many",
    ],
)
async def test_a_malformed_form_is_refused_and_saves_nothing(
    session: AsyncSession, learner: Learner, lemmas: list[str], sentences: list[str]
) -> None:
    assert learner.id is not None

    with pytest.raises(InvalidAddForm):
        await add_words(session, learner.id, lemmas, sentences, NOW)

    assert await _cards(session) == 0


async def test_an_empty_box_is_refused_without_asking_the_model(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None

    with pytest.raises(InvalidLookup) as error:
        await look_up_text(session, llm, learner.id, " \n ")

    assert error.value.problem == LookupProblem.EMPTY
    assert llm.prompts == []


async def test_too_many_lines_are_refused_without_asking_the_model(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    text = "\n".join(f"palabra{i}" for i in range(MAX_WORDS + 1))

    with pytest.raises(InvalidLookup) as error:
        await look_up_text(session, llm, learner.id, text)

    assert error.value.problem == LookupProblem.TOO_MANY
    assert llm.prompts == []


async def test_a_typed_list_is_parsed_and_looked_up(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NIETO)

    [result] = await look_up_text(session, llm, learner.id, " Nieto \n\nnieto")

    assert result.word == "nieto" and result.lookup is not None


async def test_the_search_is_trimmed_before_the_words_are_found(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    nieto, aunque = (LexemeFactory.build(lemma=lemma) for lemma in ("nieto", "aunque"))
    session.add_all([nieto, aunque])
    await session.flush()
    assert nieto.id is not None and aunque.id is not None
    await save_word(session, learner.id, nieto.id, "Mi nieto juega.", NOW)
    await save_word(session, learner.id, aunque.id, "Aunque llueve, salimos.", NOW)

    words = await find_saved_words(session, learner.id, "  NIETO ")

    assert [word.lemma for word in words] == ["nieto"]


async def test_the_vocabulary_map_counts_the_learners_words(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    vocabulary = await vocabulary_map(session, learner.id)

    assert vocabulary.known == 0
