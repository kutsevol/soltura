from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.grammar.units import all_units
from soltura.learner.repository import JournalError, save_journal_entry
from soltura.llm.client import LLMClient
from soltura.writing.service import MAX_PROMPT_LENGTH, Segment, check_length, correct_text


@dataclass(frozen=True)
class JournalResult:
    entry_id: int
    prompt: str | None
    body: str
    corrected: str
    errors: list[JournalError]
    segments: list[Segment]


async def submit_entry(
    session: AsyncSession, llm: LLMClient, learner_id: int, prompt: str | None, text: str
) -> JournalResult:
    body = text.strip()
    check_length(body)
    units = {unit.id: unit.title for unit in all_units()}
    result = await correct_text(llm, body, units)
    prompt = (prompt or "").strip()[:MAX_PROMPT_LENGTH] or None
    entry = await save_journal_entry(
        session, learner_id, prompt, body, result.corrected, result.errors
    )
    assert entry.id is not None
    return JournalResult(
        entry_id=entry.id,
        prompt=prompt,
        body=body,
        corrected=result.corrected,
        errors=result.errors,
        segments=result.segments,
    )
