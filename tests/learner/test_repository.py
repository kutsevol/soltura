from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import KnowledgeType, Learner, Lexeme
from soltura.learner.repository import get_due_cards, get_lexemes_by_lemmas, get_or_create_learner
from tests.factories import MemoryCardFactory

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


async def test_get_or_create_learner_returns_the_same_row(session: AsyncSession) -> None:
    first = await get_or_create_learner(session, telegram_user_id=4242)
    second = await get_or_create_learner(session, telegram_user_id=4242)

    assert first.id is not None
    assert second.id == first.id


async def test_get_lexemes_by_lemmas_skips_unknown_lemmas(
    session: AsyncSession, lexemes: list[Lexeme]
) -> None:
    found = await get_lexemes_by_lemmas(session, ["ser", "aunque", "zzz", "ser"])

    assert sorted(lexeme.lemma for lexeme in found) == ["aunque", "ser"]


async def test_get_due_cards_returns_only_the_learners_due_cards_oldest_first(
    session: AsyncSession, learner: Learner, other_learner: Learner, lexemes: list[Lexeme]
) -> None:
    ser, estar, aunque = lexemes
    older = MemoryCardFactory.build(
        learner_id=learner.id,
        lexeme_id=estar.id,
        knowledge_type=KnowledgeType.RECALL,
        due=NOW - timedelta(days=2),
    )
    newer = MemoryCardFactory.build(
        learner_id=learner.id,
        lexeme_id=ser.id,
        knowledge_type=KnowledgeType.RECOGNIZE,
        due=NOW - timedelta(hours=1),
    )
    not_yet_due = MemoryCardFactory.build(
        learner_id=learner.id,
        lexeme_id=aunque.id,
        knowledge_type=KnowledgeType.RECOGNIZE,
        due=NOW + timedelta(minutes=1),
    )
    someone_elses = MemoryCardFactory.build(
        learner_id=other_learner.id,
        lexeme_id=ser.id,
        knowledge_type=KnowledgeType.RECOGNIZE,
        due=NOW - timedelta(days=5),
    )
    session.add_all([older, newer, not_yet_due, someone_elses])
    await session.flush()

    assert learner.id is not None
    due = await get_due_cards(session, learner_id=learner.id, now=NOW, limit=10)

    assert [card.id for card in due] == [older.id, newer.id]


async def test_get_due_cards_stops_at_the_limit(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    session.add_all(
        MemoryCardFactory.build(
            learner_id=learner.id,
            lexeme_id=lexeme.id,
            knowledge_type=KnowledgeType.RECOGNIZE,
            due=NOW - timedelta(days=index),
        )
        for index, lexeme in enumerate(lexemes, start=1)
    )
    await session.flush()

    assert learner.id is not None
    due = await get_due_cards(session, learner_id=learner.id, now=NOW, limit=2)

    assert len(due) == 2
