from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.grammar.units import all_units
from soltura.learner.models import Rating, ReviewSource
from soltura.learner.repository import (
    JournalError,
    get_errors_for_entries,
    get_journal_entries,
    get_learner_errors,
    get_lexemes_by_lemmas,
    get_recall_cards,
    save_journal_entry,
)
from soltura.llm.client import LLMClient
from soltura.srs.service import review
from soltura.writing.prompts import PROMPTS
from soltura.writing.service import (
    ErrorCategory,
    Segment,
    build_error_summary,
    check_length,
    correct_text,
    diff_segments,
    words_written_correctly,
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
    session: AsyncSession,
    llm: LLMClient,
    learner_id: int,
    prompt: str | None,
    text: str,
    now: datetime,
) -> JournalResult:
    body = text.replace("\r\n", "\n").strip()
    check_length(body)
    units = {unit.id: unit.title for unit in all_units()}
    result = await correct_text(llm, body, units)
    prompt = prompt if prompt in PROMPTS else None
    entry = await save_journal_entry(
        session, learner_id, prompt, body, result.corrected, result.errors
    )
    assert entry.id is not None
    await review_written_words(session, learner_id, body, result.errors, now)
    return JournalResult(
        entry_id=entry.id,
        prompt=prompt,
        created_at=entry.created_at,
        body=body,
        corrected=result.corrected,
        errors=result.errors,
        segments=result.segments,
    )


async def review_written_words(
    session: AsyncSession,
    learner_id: int,
    body: str,
    errors: list[JournalError],
    now: datetime,
) -> None:
    lexemes = await get_lexemes_by_lemmas(session, words_written_correctly(body, errors))
    cards = await get_recall_cards(
        session, learner_id, [lexeme.id for lexeme in lexemes if lexeme.id is not None]
    )
    # Writing a word right is evidence of recall, never of failure: the model's
    # classification of an error is not reliable enough to lower a card.
    for card in cards:
        await review(session, card, Rating.GOOD, ReviewSource.WRITING, now)


async def journal_history(session: AsyncSession, learner_id: int) -> list[JournalResult]:
    entries = await get_journal_entries(session, learner_id, HISTORY_SIZE)
    errors = await get_errors_for_entries(
        session, [entry.id for entry in entries if entry.id is not None]
    )
    # An entry may name a unit that was renamed or removed since; it then has no lesson to link.
    known = {unit.id for unit in all_units()}
    return [
        JournalResult(
            entry_id=entry.id,
            prompt=entry.prompt,
            created_at=entry.created_at,
            body=entry.body,
            corrected=entry.corrected,
            errors=[
                JournalError(
                    e.kind,
                    e.unit_id if e.unit_id in known else None,
                    e.original,
                    e.corrected,
                    e.note,
                )
                for e in errors.get(entry.id, [])
            ],
            segments=diff_segments(entry.body, entry.corrected),
        )
        for entry in entries
        if entry.id is not None
    ]


async def error_summary(session: AsyncSession, learner_id: int) -> list[ErrorCategory]:
    errors = await get_learner_errors(session, learner_id)
    return build_error_summary(
        [JournalError(e.kind, e.unit_id, e.original, e.corrected, e.note) for e in errors],
        {unit.id: unit.title for unit in all_units()},
    )
