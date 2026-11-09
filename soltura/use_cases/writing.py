from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.grammar.units import all_units
from soltura.learner.repository import (
    JournalError,
    get_errors_for_entries,
    get_journal_entries,
    save_journal_entry,
)
from soltura.llm.client import LLMClient
from soltura.writing.service import (
    MAX_PROMPT_LENGTH,
    Segment,
    check_length,
    correct_text,
    diff_segments,
)

HISTORY_SIZE = 10


@dataclass(frozen=True)
class JournalResult:
    entry_id: int
    prompt: str | None
    created_at: datetime
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
        created_at=entry.created_at,
        body=body,
        corrected=result.corrected,
        errors=result.errors,
        segments=result.segments,
    )


async def journal_history(session: AsyncSession, learner_id: int) -> list[JournalResult]:
    entries = await get_journal_entries(session, learner_id, HISTORY_SIZE)
    errors = await get_errors_for_entries(
        session, [entry.id for entry in entries if entry.id is not None]
    )
    return [
        JournalResult(
            entry_id=entry.id,
            prompt=entry.prompt,
            created_at=entry.created_at,
            body=entry.body,
            corrected=entry.corrected,
            errors=[
                JournalError(e.kind, e.unit_id, e.original, e.corrected, e.note)
                for e in errors.get(entry.id, [])
            ],
            segments=diff_segments(entry.body, entry.corrected),
        )
        for entry in entries
        if entry.id is not None
    ]
