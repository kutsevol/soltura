import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import ErrorKind, Learner
from soltura.learner.repository import get_errors_for_entries, get_journal_entries
from soltura.llm.client import LLMUnavailableError
from soltura.use_cases.writing import submit_entry
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

    result = await submit_entry(session, llm, learner.id, "  Una nota  ", f"  {TEXT}\n")

    entries = await get_journal_entries(session, learner.id, limit=5)
    errors = await get_errors_for_entries(session, [result.entry_id])
    assert [(entry.id, entry.prompt, entry.body, entry.corrected) for entry in entries] == [
        (result.entry_id, "Una nota", TEXT, FIXED)
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
