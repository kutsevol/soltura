from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import KnowledgeType, Learner, Lexeme, UnitKind
from soltura.learner.repository import (
    BandCounts,
    count_due_cards,
    get_due_cards,
    get_latest_placement_run,
    get_lexemes_by_lemmas,
    get_or_create_learner,
    get_recent_titles,
    get_vocabulary_bands,
    save_placement_run,
    save_reading_text,
)
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
    due = await get_due_cards(
        session, learner_id=learner.id, now=NOW, limit=10, unit_kind=UnitKind.WORD
    )

    assert [card.id for card in due] == [older.id, newer.id]


async def test_get_vocabulary_bands_counts_the_learners_words_per_band(
    session: AsyncSession, learner: Learner, vocabulary_words: None
) -> None:
    assert learner.id is not None

    bands = await get_vocabulary_bands(
        session, learner.id, [(1, 250), (251, 500), (501, 10_000), (20_000, 30_000)]
    )

    # Names, words the seed never ranked and another learner's words count nowhere.
    assert bands == [
        BandCounts(total=3, known=1, learning=1),
        BandCounts(total=1, known=1, learning=0),
        BandCounts(total=1, known=0, learning=0),
        BandCounts(total=0, known=0, learning=0),
    ]


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
    due = await get_due_cards(
        session, learner_id=learner.id, now=NOW, limit=2, unit_kind=UnitKind.WORD
    )

    assert len(due) == 2


async def test_due_cards_are_asked_for_by_unit_kind(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    word = MemoryCardFactory.build(
        learner_id=learner.id,
        lexeme_id=lexemes[0].id,
        knowledge_type=KnowledgeType.RECOGNIZE,
        due=NOW - timedelta(days=1),
    )
    conjugation = MemoryCardFactory.build(
        learner_id=learner.id,
        unit_kind=UnitKind.CONJUGATION,
        unit_key="tener|preterite|ellos",
        lexeme_id=None,
        knowledge_type=KnowledgeType.RECALL,
        due=NOW - timedelta(days=2),
    )
    session.add_all([word, conjugation])
    await session.flush()

    assert learner.id is not None
    words = await get_due_cards(
        session, learner_id=learner.id, now=NOW, limit=10, unit_kind=UnitKind.WORD
    )
    conjugations = await get_due_cards(
        session, learner_id=learner.id, now=NOW, limit=10, unit_kind=UnitKind.CONJUGATION
    )

    assert [card.id for card in words] == [word.id]
    assert [card.id for card in conjugations] == [conjugation.id]
    assert await count_due_cards(session, learner.id, NOW, UnitKind.WORD) == 1
    assert await count_due_cards(session, learner.id, NOW, UnitKind.CONJUGATION) == 1
    assert await count_due_cards(session, learner.id, NOW, UnitKind.GRAMMAR) == 0


async def test_the_latest_placement_run_is_the_learners_newest(
    session: AsyncSession, learner: Learner, other_learner: Learner
) -> None:
    assert learner.id is not None and other_learner.id is not None
    bands = [{"band": 0, "max_rank": 250, "correct": 5, "total": 5}]
    await save_placement_run(session, learner.id, 0, bands)
    newest = await save_placement_run(session, learner.id, 250, bands)
    await save_placement_run(session, other_learner.id, 500, bands)

    latest = await get_latest_placement_run(session, learner.id)

    assert latest is not None
    assert (latest.id, latest.known_rank, latest.bands) == (newest.id, 250, bands)


async def test_a_learner_without_a_placement_run_has_none(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    assert await get_latest_placement_run(session, learner.id) is None


async def test_recent_titles_are_the_learners_newest_first_and_limited(
    session: AsyncSession, learner: Learner, other_learner: Learner
) -> None:
    assert learner.id is not None and other_learner.id is not None
    for title in ("uno", "dos", "tres"):
        await save_reading_text(session, learner.id, None, title)
    await save_reading_text(session, other_learner.id, None, "ajeno")

    assert await get_recent_titles(session, learner.id, 2) == ["tres", "dos"]
