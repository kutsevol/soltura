import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import ErrorKind, Learner
from soltura.learner.repository import get_errors_for_entries, get_journal_entries
from soltura.llm.client import LLMUnavailableError
from soltura.use_cases.writing import HISTORY_SIZE, error_summary, journal_history, submit_entry
from soltura.writing.prompts import PROMPTS
from soltura.writing.service import Correction, FoundError, InvalidText, TextProblem
from tests.fakes import FakeLLM

TEXT = "Yo soy cansado porque trabajo mucho."
FIXED = "Estoy cansado porque trabajo mucho."


async def test_a_submitted_text_is_saved_with_its_errors(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(
        Correction(
            corrected_text=FIXED,
            errors=[
                FoundError(original="Yo soy", corrected="Estoy", category="ser_estar", note="Стан.")
            ],
        )
    )

    result = await submit_entry(session, llm, learner.id, PROMPTS[0], f"  {TEXT}\n")

    entries = await get_journal_entries(session, learner.id, limit=5)
    errors = await get_errors_for_entries(session, [result.entry_id])
    assert [(entry.id, entry.prompt, entry.body, entry.corrected) for entry in entries] == [
        (result.entry_id, PROMPTS[0], TEXT, FIXED)
    ]
    assert [(error.kind, error.unit_id, error.original) for error in errors[result.entry_id]] == [
        (ErrorKind.GRAMMAR, "ser_estar", "Yo soy")
    ]
    assert result.corrected == FIXED
    assert "ser_estar" in llm.prompts[0]


@pytest.mark.parametrize(
    ("text", "problem"),
    [("Hola.", TextProblem.TOO_SHORT), ("a" * 1_001, TextProblem.TOO_LONG)],
)
async def test_a_text_of_the_wrong_length_is_refused_before_the_model_is_called(
    session: AsyncSession, learner: Learner, llm: FakeLLM, text: str, problem: TextProblem
) -> None:
    assert learner.id is not None

    with pytest.raises(InvalidText) as raised:
        await submit_entry(session, llm, learner.id, None, text)

    assert raised.value.problem == problem
    assert llm.prompts == []


async def test_a_model_failure_saves_nothing(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.fail(Correction, LLMUnavailableError("down"))

    with pytest.raises(LLMUnavailableError):
        await submit_entry(session, llm, learner.id, None, TEXT)

    assert await get_journal_entries(session, learner.id, limit=5) == []


async def test_a_prompt_that_is_not_one_of_the_tasks_is_not_stored(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    result = await submit_entry(session, llm, learner.id, "forged task", TEXT)

    assert result.prompt is None


async def test_a_newline_counts_once_toward_the_length_limit(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    text = "\r\n".join(["a" * 99] * 10)
    llm.answer(Correction(corrected_text=text, errors=[]))

    result = await submit_entry(session, llm, learner.id, None, text)

    assert result.body == "\n".join(["a" * 99] * 10)


@pytest.mark.parametrize(
    ("length", "accepted"), [(19, False), (20, True), (1_000, True), (1_001, False)]
)
async def test_the_length_limits_are_inclusive(
    session: AsyncSession, learner: Learner, llm: FakeLLM, length: int, accepted: bool
) -> None:
    assert learner.id is not None
    text = "a" * length
    llm.answer(Correction(corrected_text=text, errors=[]))

    if accepted:
        await submit_entry(session, llm, learner.id, None, text)
    else:
        with pytest.raises(InvalidText):
            await submit_entry(session, llm, learner.id, None, text)


async def test_the_history_is_the_newest_texts_of_this_learner_only(
    session: AsyncSession, learner: Learner, other_learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None and other_learner.id is not None
    for number in range(HISTORY_SIZE + 2):
        text = f"{TEXT} {number}"
        llm.answer(Correction(corrected_text=text, errors=[]))
        await submit_entry(session, llm, learner.id, None, text)
    llm.answer(Correction(corrected_text=TEXT, errors=[]))
    await submit_entry(session, llm, other_learner.id, None, TEXT)

    history = await journal_history(session, learner.id)

    assert [entry.body for entry in history] == [
        f"{TEXT} {number}" for number in range(HISTORY_SIZE + 1, 1, -1)
    ]


async def test_the_error_summary_counts_only_this_learners_errors(
    session: AsyncSession, learner: Learner, other_learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None and other_learner.id is not None
    correction = Correction(
        corrected_text=FIXED,
        errors=[FoundError(original="Yo soy", corrected="Estoy", category="ser_estar", note="n")],
    )
    for learner_id in (learner.id, other_learner.id, other_learner.id):
        llm.answer(correction)
        await submit_entry(session, llm, learner_id, None, TEXT)

    summary = await error_summary(session, learner.id)

    assert [(c.unit_id, c.count) for c in summary] == [("ser_estar", 1)]
