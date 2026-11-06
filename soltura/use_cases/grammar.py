from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.grammar.service import (
    GRAMMAR_RATING,
    SESSION_SIZE,
    ExerciseResult,
    GrammarItem,
    GrammarProgress,
    build_progress,
    check_exercise,
)
from soltura.grammar.units import (
    GrammarUnit,
    get_unit,
    next_unit,
    parse_exercise_key,
    started_unit_ids,
    unit_keys,
)
from soltura.learner.models import KnowledgeType, MemoryCard, ReviewSource, UnitKind
from soltura.learner.repository import get_card_progress, get_unit_keys
from soltura.srs.service import due_queue, review, schedule_units


@dataclass(frozen=True)
class GrammarState:
    items: list[GrammarItem]
    lesson: GrammarUnit | None


async def next_lesson(session: AsyncSession, learner_id: int) -> GrammarUnit | None:
    keys = await get_unit_keys(session, learner_id, UnitKind.GRAMMAR)
    return next_unit(started_unit_ids(keys))


async def grammar_state(session: AsyncSession, learner_id: int, now: datetime) -> GrammarState:
    # Retrieval comes before new input: the next lesson is offered only when no
    # exercise is due.
    cards = await due_queue(
        session, learner_id, now=now, limit=SESSION_SIZE, unit_kind=UnitKind.GRAMMAR
    )
    items: list[GrammarItem] = []
    for card in cards:
        parsed = parse_exercise_key(card.unit_key)
        if card.id is not None and parsed is not None:
            items.append(GrammarItem(card.id, parsed[0].id, parsed[1].id))
    if items:
        return GrammarState(items=items, lesson=None)
    return GrammarState(items=[], lesson=await next_lesson(session, learner_id))


async def start_unit(
    session: AsyncSession, learner_id: int, unit_id: str, now: datetime
) -> GrammarUnit:
    unit = get_unit(unit_id)
    if unit is None:
        raise LookupError(f"No grammar unit {unit_id}")
    await schedule_units(
        session, learner_id, UnitKind.GRAMMAR, unit_keys(unit), KnowledgeType.RECALL, now
    )
    return unit


async def answer_exercise(
    session: AsyncSession,
    learner_id: int,
    card_id: int,
    answer: str,
    duration_ms: int | None,
    now: datetime,
) -> ExerciseResult:
    card = await session.get(MemoryCard, card_id)
    if card is None or card.learner_id != learner_id or card.unit_kind != UnitKind.GRAMMAR:
        raise PermissionError("This card does not belong to the learner")
    parsed = parse_exercise_key(card.unit_key)
    if parsed is None:
        raise ValueError(f"Card {card_id} does not name a grammar exercise")
    unit, exercise = parsed

    check = check_exercise(exercise, answer)
    rating = GRAMMAR_RATING[check]
    await review(
        session,
        card,
        rating,
        ReviewSource.GRAMMAR,
        now,
        answer=answer.strip() or None,
        duration_ms=duration_ms,
    )
    return ExerciseResult(
        rating=rating, check=check, expected=exercise.answer, note=exercise.note, unit_id=unit.id
    )


async def grammar_progress(session: AsyncSession, learner_id: int) -> GrammarProgress:
    return build_progress(await get_card_progress(session, learner_id, UnitKind.GRAMMAR))
