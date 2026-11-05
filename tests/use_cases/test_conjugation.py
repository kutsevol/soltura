from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.conjugation.forms import Person, Tense
from soltura.learner.models import (
    KnowledgeType,
    Learner,
    Lexeme,
    MemoryCard,
    Rating,
    ReviewLog,
    ReviewSource,
    UnitKind,
)
from soltura.srs.service import save_word, schedule_units
from soltura.use_cases.conjugation import answer_item, build_session

NOW = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)


async def _conjugation_cards(session: AsyncSession) -> list[MemoryCard]:
    result = await session.execute(
        select(MemoryCard)
        .where(col(MemoryCard.unit_kind) == UnitKind.CONJUGATION)
        .order_by(col(MemoryCard.id))
    )
    return list(result.scalars())


async def _schedule(session: AsyncSession, learner: Learner, key: str) -> int:
    assert learner.id is not None
    await schedule_units(
        session, learner.id, UnitKind.CONJUGATION, [key], KnowledgeType.RECALL, NOW
    )
    card = next(card for card in await _conjugation_cards(session) if card.unit_key == key)
    assert card.id is not None
    return card.id


async def test_a_new_learner_is_offered_the_most_frequent_verb_in_the_present_in_every_person(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None

    items = await build_session(session, learner.id, NOW)

    assert [(item.verb, item.tense, item.person) for item in items] == [
        ("ser", Tense.PRESENT, person) for person in Person
    ]
    cards = await _conjugation_cards(session)
    assert len(cards) == 6
    assert all(card.knowledge_type == KnowledgeType.RECALL and card.due == NOW for card in cards)


async def test_another_set_waits_until_the_last_one_has_been_answered(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    first = await build_session(session, learner.id, NOW)

    again = await build_session(session, learner.id, NOW)

    assert [item.card_id for item in again] == [item.card_id for item in first]
    assert len(await _conjugation_cards(session)) == 6


async def test_the_next_set_arrives_once_the_last_one_is_answered_and_the_answered_cards_wait(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    first = await build_session(session, learner.id, NOW)
    for item in first:
        await answer_item(session, learner.id, item.card_id, "x", 1000, NOW)

    items = await build_session(session, learner.id, NOW)

    assert [(item.verb, item.tense) for item in items] == [("ser", Tense.PRETERITE)] * 6
    assert {item.card_id for item in items}.isdisjoint(item.card_id for item in first)


async def test_an_answered_card_returns_on_the_fsrs_schedule_and_not_before(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    first = await build_session(session, learner.id, NOW)
    answered = first[0]
    await answer_item(session, learner.id, answered.card_id, "soy", 1500, NOW)
    card = await session.get(MemoryCard, answered.card_id)
    assert card is not None

    before = await build_session(session, learner.id, NOW)
    on_schedule = await build_session(session, learner.id, card.due)

    assert card.due > NOW
    assert answered.card_id not in {item.card_id for item in before}
    assert len(before) == 5
    assert answered.card_id in {item.card_id for item in on_schedule}


@pytest.mark.parametrize(
    ("key", "answer", "rating"),
    [
        ("tener|preterite|ellos", "tuvieron", Rating.GOOD),
        ("tener|preterite|ellos", " Tuvieron. ", Rating.GOOD),
        ("tener|present|vosotros", "teneis", Rating.HARD),
        ("tener|preterite|ellos", "tuvieran", Rating.AGAIN),
        ("tener|present|yo", "tener", Rating.AGAIN),
        ("tener|present|yo", "", Rating.AGAIN),
    ],
)
async def test_the_answer_is_rated_by_how_close_the_form_is(
    session: AsyncSession, learner: Learner, key: str, answer: str, rating: Rating
) -> None:
    assert learner.id is not None
    card_id = await _schedule(session, learner, key)

    result = await answer_item(session, learner.id, card_id, answer, 2000, NOW)

    assert result.rating == rating


async def test_an_answer_shows_the_right_form_and_is_logged_as_a_conjugation_review(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    card_id = await _schedule(session, learner, "tener|preterite|ellos")

    result = await answer_item(session, learner.id, card_id, "tuvieran", 2000, NOW)

    assert result.expected == "tuvieron"
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [(log.card_id, log.rating, log.source, log.answer, log.duration_ms) for log in logs] == [
        (card_id, Rating.AGAIN, ReviewSource.CONJUGATION, "tuvieran", 2000)
    ]


async def test_a_card_of_someone_else_or_of_another_kind_cannot_be_answered(
    session: AsyncSession,
    learner: Learner,
    verb_lexemes: list[Lexeme],
    due_conjugation_card: MemoryCard,
) -> None:
    assert learner.id is not None and due_conjugation_card.id is not None
    assert verb_lexemes[4].id is not None
    word_card, _ = await save_word(session, learner.id, verb_lexemes[4].id, "Soy yo.", NOW)
    assert word_card.id is not None

    with pytest.raises(PermissionError):
        await answer_item(session, learner.id + 1, due_conjugation_card.id, "tuvieron", None, NOW)
    with pytest.raises(PermissionError):
        await answer_item(session, learner.id, word_card.id, "soy", None, NOW)
