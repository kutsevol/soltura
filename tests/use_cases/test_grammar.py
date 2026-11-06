from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.grammar.units import all_units, unit_keys
from soltura.learner.models import (
    KnowledgeType,
    Learner,
    MemoryCard,
    Rating,
    ReviewLog,
    ReviewSource,
    UnitKind,
)
from soltura.srs.service import schedule_units
from soltura.use_cases.grammar import (
    answer_exercise,
    grammar_progress,
    grammar_state,
    next_lesson,
    start_unit,
)
from tests.factories import LearnerFactory

NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
FIRST, SECOND = all_units()[:2]


async def _grammar_cards(session: AsyncSession) -> list[MemoryCard]:
    result = await session.execute(
        select(MemoryCard)
        .where(col(MemoryCard.unit_kind) == UnitKind.GRAMMAR)
        .order_by(col(MemoryCard.id))
    )
    return list(result.scalars())


async def _card_id(session: AsyncSession, key: str) -> int:
    card = next(card for card in await _grammar_cards(session) if card.unit_key == key)
    assert card.id is not None
    return card.id


async def test_a_new_learner_is_offered_the_first_lesson_and_no_exercises(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    state = await grammar_state(session, learner.id, NOW)

    assert state.items == []
    assert state.lesson == FIRST
    assert await _grammar_cards(session) == []


async def test_starting_a_unit_schedules_its_six_exercises_as_due_cards(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    await start_unit(session, learner.id, FIRST.id, NOW)
    state = await grammar_state(session, learner.id, NOW)

    cards = await _grammar_cards(session)
    assert [card.unit_key for card in cards] == unit_keys(FIRST)
    assert all(card.due == NOW and card.knowledge_type == KnowledgeType.RECALL for card in cards)
    assert state.lesson is None
    assert {(item.unit_id, item.exercise_id) for item in state.items} == {
        (FIRST.id, exercise.id) for exercise in FIRST.exercises
    }


async def test_starting_a_unit_again_adds_no_cards(session: AsyncSession, learner: Learner) -> None:
    assert learner.id is not None
    await start_unit(session, learner.id, FIRST.id, NOW)

    await start_unit(session, learner.id, FIRST.id, NOW)

    assert len(await _grammar_cards(session)) == 6


async def test_a_unit_that_does_not_exist_cannot_be_started(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    with pytest.raises(LookupError):
        await start_unit(session, learner.id, "nothing", NOW)


async def test_the_next_lesson_comes_only_when_no_exercise_is_due(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_unit(session, learner.id, FIRST.id, NOW)
    items = (await grammar_state(session, learner.id, NOW)).items
    assert await next_lesson(session, learner.id) == SECOND

    for item in items[:-1]:
        await answer_exercise(session, learner.id, item.card_id, "x", 1000, NOW)
    still_due = await grammar_state(session, learner.id, NOW)
    await answer_exercise(session, learner.id, items[-1].card_id, "x", 1000, NOW)
    none_due = await grammar_state(session, learner.id, NOW)

    assert len(still_due.items) == 1 and still_due.lesson is None
    assert none_due.items == [] and none_due.lesson == SECOND


@pytest.mark.parametrize(
    ("answer", "rating"),
    [
        ("es", Rating.GOOD),
        ("está", Rating.AGAIN),
        ("", Rating.AGAIN),
    ],
)
async def test_a_choice_is_rated_by_whether_it_is_the_stored_answer(
    session: AsyncSession, learner: Learner, answer: str, rating: Rating
) -> None:
    assert learner.id is not None
    unit = next(unit for unit in all_units() if unit.id == "ser_estar")
    await start_unit(session, learner.id, unit.id, NOW)
    card_id = await _card_id(session, f"{unit.id}|e1")

    result = await answer_exercise(session, learner.id, card_id, answer, 2000, NOW)

    assert result.rating == rating
    assert result.expected == "es"
    assert result.note == unit.exercises[0].note


@pytest.mark.parametrize(
    ("answer", "rating"),
    [("están", Rating.GOOD), ("estan", Rating.HARD), ("es", Rating.AGAIN)],
)
async def test_a_typed_word_is_rated_by_how_close_it_is_to_the_stored_one(
    session: AsyncSession, learner: Learner, answer: str, rating: Rating
) -> None:
    assert learner.id is not None
    await start_unit(session, learner.id, "ser_estar", NOW)
    card_id = await _card_id(session, "ser_estar|e6")

    result = await answer_exercise(session, learner.id, card_id, answer, 2000, NOW)

    assert result.rating == rating


async def test_an_answer_is_logged_as_a_grammar_review_and_the_card_waits_for_its_schedule(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_unit(session, learner.id, "ser_estar", NOW)
    card_id = await _card_id(session, "ser_estar|e1")

    await answer_exercise(session, learner.id, card_id, "es", 1500, NOW)

    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [(log.card_id, log.rating, log.source, log.answer, log.duration_ms) for log in logs] == [
        (card_id, Rating.GOOD, ReviewSource.GRAMMAR, "es", 1500)
    ]
    card = await session.get(MemoryCard, card_id)
    assert card is not None and card.due > NOW
    before = await grammar_state(session, learner.id, NOW)
    later = await grammar_state(session, learner.id, card.due + timedelta(seconds=1))
    assert card_id not in {item.card_id for item in before.items}
    assert card_id in {item.card_id for item in later.items}


async def test_a_card_of_someone_else_or_of_another_kind_cannot_be_answered(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    other = LearnerFactory.build()
    session.add(other)
    await session.flush()
    assert other.id is not None
    await start_unit(session, other.id, FIRST.id, NOW)
    theirs = await _card_id(session, unit_keys(FIRST)[0])
    await schedule_units(
        session, learner.id, UnitKind.CONJUGATION, ["ser|present|yo"], KnowledgeType.RECALL, NOW
    )
    conjugation = next(
        card
        for card in (await session.execute(select(MemoryCard))).scalars()
        if card.unit_kind == UnitKind.CONJUGATION
    )
    assert conjugation.id is not None

    with pytest.raises(PermissionError):
        await answer_exercise(session, learner.id, theirs, "es", 1000, NOW)
    with pytest.raises(PermissionError):
        await answer_exercise(session, learner.id, conjugation.id, "es", 1000, NOW)
    with pytest.raises(PermissionError):
        await answer_exercise(session, learner.id, 999_999, "es", 1000, NOW)


async def test_a_new_learner_has_no_progress_and_every_unit_not_started(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    progress = await grammar_progress(session, learner.id)

    assert progress.units == []
    assert progress.not_started == len(all_units())


async def test_progress_lists_the_started_units_with_their_answers_and_solid_cards(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_unit(session, learner.id, FIRST.id, NOW)
    cards = {card.unit_key: card for card in await _grammar_cards(session)}
    first, second = (cards[key] for key in unit_keys(FIRST)[:2])
    assert first.id is not None and second.id is not None
    await answer_exercise(session, learner.id, first.id, FIRST.exercises[0].answer, 1000, NOW)
    await answer_exercise(session, learner.id, first.id, "x", 1000, NOW)
    await answer_exercise(session, learner.id, second.id, "x", 1000, NOW)

    progress = await grammar_progress(session, learner.id)

    assert progress.not_started == len(all_units()) - 1
    [unit] = progress.units
    assert unit.unit == FIRST
    assert (unit.answers, unit.right, unit.solid) == (3, 1, 0)
    assert unit.next_due == min(card.due for card in await _grammar_cards(session))
