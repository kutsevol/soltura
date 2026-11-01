import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner
from soltura.words.service import (
    NotASpanishWordError,
    WordEntry,
    WordLookupFailedError,
    look_up_word,
)
from tests.fakes import FakeLLM

NIETO = WordEntry(
    is_spanish_word=True, lemma="nieto", translation="онук", sentence="Mi nieto juega en el parque."
)


async def test_a_typed_word_comes_back_with_a_sentence_that_contains_it(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NIETO)

    lookup = await look_up_word(session, llm, learner.id, "nieto")

    assert (lookup.lemma, lookup.translation, lookup.saved) == ("nieto", "онук", False)
    assert "nieto" in lookup.sentence


async def test_an_inflected_input_resolves_to_its_lemma_and_form_in_the_sentence(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(
        WordEntry(
            is_spanish_word=True,
            lemma="nieto",
            translation="онук",
            sentence="Mis nietos viven en Madrid.",
        )
    )

    lookup = await look_up_word(session, llm, learner.id, "nietos")

    assert lookup.lemma == "nieto"


async def test_a_sentence_without_the_word_is_retried_once(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(NIETO.model_copy(update={"sentence": "Hoy hace sol."}), NIETO)

    lookup = await look_up_word(session, llm, learner.id, "nieto")

    assert lookup.sentence == NIETO.sentence
    assert len(llm.prompts) == 2


async def test_a_lookup_fails_when_the_retry_also_lacks_the_word(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(*[NIETO.model_copy(update={"sentence": "Hoy hace sol."})] * 2)

    with pytest.raises(WordLookupFailedError):
        await look_up_word(session, llm, learner.id, "nieto")

    assert len(llm.prompts) == 2


async def test_a_word_that_is_not_spanish_is_refused(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(WordEntry(is_spanish_word=False, lemma="", translation="", sentence=""))

    with pytest.raises(NotASpanishWordError):
        await look_up_word(session, llm, learner.id, "asdfg")


async def test_a_word_already_being_learned_is_reported_saved(
    session: AsyncSession, learner: Learner, llm: FakeLLM, saved_words: None
) -> None:
    assert learner.id is not None
    llm.answer(NIETO)

    lookup = await look_up_word(session, llm, learner.id, "nieto")

    assert lookup.saved
