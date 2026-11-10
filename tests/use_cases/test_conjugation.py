from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.config import settings
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

    items = (await build_session(session, learner.id, NOW)).items

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
    first = (await build_session(session, learner.id, NOW)).items

    again = (await build_session(session, learner.id, NOW)).items

    assert [item.card_id for item in again] == [item.card_id for item in first]
    assert len(await _conjugation_cards(session)) == 6


async def test_the_next_set_arrives_once_the_last_one_is_answered_and_the_answered_cards_wait(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    first = (await build_session(session, learner.id, NOW)).items
    for item in first:
        await answer_item(session, learner.id, item.card_id, "x", 1000, NOW)

    items = (await build_session(session, learner.id, NOW)).items

    assert [(item.verb, item.tense) for item in items] == [("ser", Tense.PRETERITE)] * 6
    assert {item.card_id for item in items}.isdisjoint(item.card_id for item in first)


async def test_an_answered_card_returns_on_the_fsrs_schedule_and_not_before(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    first = (await build_session(session, learner.id, NOW)).items
    answered = first[0]
    await answer_item(session, learner.id, answered.card_id, "soy", 1500, NOW)
    card = await session.get(MemoryCard, answered.card_id)
    assert card is not None

    before = (await build_session(session, learner.id, NOW)).items
    on_schedule = (await build_session(session, learner.id, card.due)).items

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


@pytest.mark.parametrize(
    ("key", "answer", "rating"),
    [
        ("haber|present|yo", "he", Rating.GOOD),
        ("haber|present|el", "ha", Rating.GOOD),
        ("haber|present|el", "hay", Rating.AGAIN),
        ("haber|preterite|yo", "hubo", Rating.AGAIN),
        ("pasar|preterite|el", "pasó", Rating.GOOD),
    ],
)
async def test_haber_and_pasar_cards_are_checked_against_their_own_forms(
    session: AsyncSession, learner: Learner, key: str, answer: str, rating: Rating
) -> None:
    assert learner.id is not None
    card_id = await _schedule(session, learner, key)

    result = await answer_item(session, learner.id, card_id, answer, 1000, NOW)

    assert result.rating == rating


async def _answer_the_whole_set(session: AsyncSession, learner: Learner) -> int:
    assert learner.id is not None
    items = (await build_session(session, learner.id, NOW)).items
    for item in items:
        await answer_item(session, learner.id, item.card_id, "x", 1000, NOW)
    return len(items)


async def test_no_new_set_starts_after_the_daily_cap_and_the_screen_says_why(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    for _ in range(4):
        assert await _answer_the_whole_set(session, learner) == 6

    held = await build_session(session, learner.id, NOW)

    assert (held.items, held.capped) == ([], True)
    assert len(await _conjugation_cards(session)) == 24


async def test_the_cap_follows_the_setting(
    session: AsyncSession,
    learner: Learner,
    verb_lexemes: list[Lexeme],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert learner.id is not None
    monkeypatch.setattr(settings.conjugation, "new_sets_per_day", 1)
    await _answer_the_whole_set(session, learner)

    assert (await build_session(session, learner.id, NOW)).capped is True


async def test_a_new_set_starts_again_a_day_after_the_first(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    for _ in range(4):
        await _answer_the_whole_set(session, learner)
    for card in await _conjugation_cards(session):
        card.created_at = NOW - timedelta(hours=25)
    await session.flush()

    study = await build_session(session, learner.id, NOW)

    assert study.capped is False
    assert [(item.verb, item.tense) for item in study.items] == [("tener", Tense.PRESENT)] * 6


async def test_cards_due_for_review_are_still_offered_when_the_cap_holds(
    session: AsyncSession, learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    for _ in range(4):
        await _answer_the_whole_set(session, learner)

    # The first moment every answered card is due; the sets were started inside the day before it.
    later = max(card.due for card in await _conjugation_cards(session))
    study = await build_session(session, learner.id, later)

    assert study.capped is True
    assert len(study.items) == 18


async def test_another_learners_sets_do_not_count_toward_the_cap(
    session: AsyncSession, learner: Learner, other_learner: Learner, verb_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None and other_learner.id is not None
    for _ in range(4):
        await _answer_the_whole_set(session, other_learner)

    study = await build_session(session, learner.id, NOW)

    assert study.capped is False
    assert len(study.items) == 6
