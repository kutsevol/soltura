import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner
from soltura.llm.client import LLMNotConfiguredError, LLMUnavailableError
from soltura.words.service import (
    Problem,
    WordEntry,
    look_up_words,
    parse_words,
)
from tests.fakes import FakeLLM, GatedLLM

NIETO = WordEntry(
    is_spanish_word=True, lemma="nieto", translation="онук", sentence="Mi nieto juega en el parque."
)
SUEGRA = WordEntry(
    is_spanish_word=True,
    lemma="suegra",
    translation="свекруха",
    sentence="Mi suegra cocina muy bien.",
)
VECINO = WordEntry(
    is_spanish_word=True, lemma="vecino", translation="сусід", sentence="Mi vecino es muy amable."
)
NO_WORD = NIETO.model_copy(update={"sentence": "Hoy hace sol."})


def test_parsing_drops_blank_lines_and_repeats_and_keeps_the_order() -> None:
    assert parse_words(" Nieto \n\nsuegra\nNIETO\n  \nvecino") == ["nieto", "suegra", "vecino"]


async def test_a_typed_word_comes_back_with_a_sentence_that_contains_it(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NIETO)

    [result] = await look_up_words(session, llm, learner.id, ["nieto"])

    assert result.lookup is not None and result.problem is None
    assert (result.lookup.lemma, result.lookup.translation, result.lookup.saved) == (
        "nieto",
        "онук",
        False,
    )
    assert "nieto" in result.lookup.sentence


async def test_an_inflected_input_resolves_to_its_lemma_and_form_in_the_sentence(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NIETO.model_copy(update={"sentence": "Mis nietos viven en Madrid."}))

    [result] = await look_up_words(session, llm, learner.id, ["nietos"])

    assert result.lookup is not None and result.lookup.lemma == "nieto"


async def test_a_sentence_without_the_word_is_retried_once(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NO_WORD, NIETO)

    [result] = await look_up_words(session, llm, learner.id, ["nieto"])

    assert result.lookup is not None and result.lookup.sentence == NIETO.sentence
    assert len(llm.prompts) == 2


async def test_a_lookup_fails_when_the_retry_also_lacks_the_word(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NO_WORD, NO_WORD)

    [result] = await look_up_words(session, llm, learner.id, ["nieto"])

    assert (result.lookup, result.problem) == (None, Problem.NO_EXAMPLE)
    assert len(llm.prompts) == 2


async def test_a_word_that_is_not_spanish_is_refused(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(WordEntry(is_spanish_word=False, lemma="", translation="", sentence=""))

    [result] = await look_up_words(session, llm, learner.id, ["asdfg"])

    assert result.problem == Problem.NOT_SPANISH


async def test_a_word_already_being_learned_is_reported_saved(
    session: AsyncSession, learner: Learner, llm: FakeLLM, saved_words: None
) -> None:
    assert learner.id is not None
    llm.answer(NIETO)

    [result] = await look_up_words(session, llm, learner.id, ["nieto"])

    assert result.lookup is not None and result.lookup.saved


async def test_the_lookups_of_a_list_run_concurrently(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    llm = GatedLLM(parties=3)
    llm.answer(NIETO, SUEGRA, VECINO)

    results = await look_up_words(session, llm, learner.id, ["nieto", "suegra", "vecino"])

    # The fake hands its answers out in the order the calls arrive, which concurrency
    # does not fix, so only the set of lemmas is compared.
    assert {result.lookup.lemma for result in results if result.lookup} == {
        "nieto",
        "suegra",
        "vecino",
    }


async def test_a_failing_line_does_not_stop_the_others(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.fail(WordEntry, LLMUnavailableError("overloaded"))
    llm.answer(SUEGRA)

    results = await look_up_words(session, llm, learner.id, ["nieto", "suegra"])

    assert [(result.word, result.problem) for result in results] == [
        ("nieto", Problem.UNAVAILABLE),
        ("suegra", None),
    ]


async def test_a_missing_api_key_fails_the_whole_list_with_its_own_error(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.fail(WordEntry, LLMNotConfiguredError("no key"))

    with pytest.raises(LLMNotConfiguredError):
        await look_up_words(session, llm, learner.id, ["nieto"])


async def test_two_lines_that_resolve_to_one_lemma_are_shown_once(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NIETO, NIETO.model_copy(update={"sentence": "Mis nietos viven en Madrid."}))

    results = await look_up_words(session, llm, learner.id, ["nieto", "nietos"])

    assert [result.word for result in results] == ["nieto"]


async def test_a_line_with_several_words_is_not_sent_to_the_model(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None

    [result] = await look_up_words(session, llm, learner.id, ["el piso"])

    assert result.problem == Problem.MULTIPLE_WORDS and llm.prompts == []
