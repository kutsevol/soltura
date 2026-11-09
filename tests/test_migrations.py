import asyncio
from datetime import UTC, datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str) -> Config:
    config = Config(ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def test_migrations_match_the_models(database_url: str) -> None:
    command.check(_alembic_config(database_url))


def test_migrations_downgrade_and_upgrade_again(database_url: str) -> None:
    config = _alembic_config(database_url)

    command.downgrade(config, "base")
    command.upgrade(config, "head")


async def _run(database_url: str, *statements: str) -> list[tuple[object, ...]]:
    engine = create_async_engine(database_url, poolclass=NullPool)
    rows: list[tuple[object, ...]] = []
    async with engine.begin() as connection:
        for statement in statements:
            result = await connection.execute(text(statement))
            rows = [tuple(row) for row in result] if result.returns_rows else []
    await engine.dispose()
    return rows


def test_existing_word_cards_keep_their_schedule_through_the_card_unit_migration(
    database_url: str,
) -> None:
    config = _alembic_config(database_url)
    due = datetime(2026, 5, 1, 9, 30, tzinfo=UTC)
    history = "state, stability, difficulty, due, last_review"
    command.downgrade(config, "0001")
    try:
        asyncio.run(
            _run(
                database_url,
                "INSERT INTO learner (id, telegram_user_id) VALUES (1, 1)",
                "INSERT INTO lexeme (id, lemma, pos, frequency_rank) VALUES (7, 'ser', 'AUX', 1)",
                """
                INSERT INTO memory_card
                    (learner_id, lexeme_id, knowledge_type, state, stability, difficulty, due,
                     last_review)
                VALUES (1, 7, 'recall', 'review', 12.5, 4.2, '2026-05-01 09:30+00',
                        '2026-04-20 09:30+00')
                """,
            )
        )
        before = asyncio.run(_run(database_url, f"SELECT {history} FROM memory_card"))

        command.upgrade(config, "head")
        card = asyncio.run(
            _run(database_url, "SELECT unit_kind, unit_key, lexeme_id FROM memory_card")
        )
        after = asyncio.run(_run(database_url, f"SELECT {history} FROM memory_card"))

        assert card == [("word", "7", 7)]
        assert after == before
        assert after[0][3] == due

        command.downgrade(config, "0001")
        assert asyncio.run(_run(database_url, f"SELECT {history} FROM memory_card")) == before
    finally:
        command.downgrade(config, "base")
        command.upgrade(config, "head")


def test_undoing_the_review_source_migration_drops_the_conjugation_reviews(
    database_url: str,
) -> None:
    config = _alembic_config(database_url)
    sources = "SELECT source::text FROM review_log"
    values = "SELECT enum_range(NULL::review_source)::text"
    try:
        asyncio.run(
            _run(
                database_url,
                "INSERT INTO learner (id, telegram_user_id) VALUES (1, 1)",
                """
                INSERT INTO memory_card (learner_id, unit_kind, unit_key, knowledge_type, due)
                VALUES (1, 'conjugation', 'ser|present|yo', 'recall', now())
                """,
                "INSERT INTO review_log (card_id, rating, source, reviewed_at) "
                "SELECT id, 'good', 'conjugation'::review_source, now() FROM memory_card",
                "INSERT INTO review_log (card_id, rating, source, reviewed_at) "
                "SELECT id, 'good', 'warmup'::review_source, now() FROM memory_card",
            )
        )

        command.downgrade(config, "0002")
        assert asyncio.run(_run(database_url, sources)) == [("warmup",)]
        assert asyncio.run(_run(database_url, values)) == [("{warmup,reading_tap}",)]

        command.upgrade(config, "head")
        assert asyncio.run(_run(database_url, values)) == [
            ("{warmup,reading_tap,conjugation,grammar,writing}",)
        ]
    finally:
        command.downgrade(config, "base")
        command.upgrade(config, "head")


def test_undoing_the_grammar_migration_drops_the_grammar_reviews(database_url: str) -> None:
    config = _alembic_config(database_url)
    sources = "SELECT source::text FROM review_log"
    values = "SELECT enum_range(NULL::review_source)::text"
    try:
        asyncio.run(
            _run(
                database_url,
                "INSERT INTO learner (id, telegram_user_id) VALUES (1, 1)",
                """
                INSERT INTO memory_card (learner_id, unit_kind, unit_key, knowledge_type, due)
                VALUES (1, 'grammar', 'ser_estar|e1', 'recall', now())
                """,
                "INSERT INTO review_log (card_id, rating, source, reviewed_at) "
                "SELECT id, 'good', 'grammar'::review_source, now() FROM memory_card",
                "INSERT INTO review_log (card_id, rating, source, reviewed_at) "
                "SELECT id, 'good', 'conjugation'::review_source, now() FROM memory_card",
            )
        )

        command.downgrade(config, "0006")
        assert asyncio.run(_run(database_url, sources)) == [("conjugation",)]
        assert asyncio.run(_run(database_url, values)) == [("{warmup,reading_tap,conjugation}",)]

        command.upgrade(config, "head")
        assert asyncio.run(_run(database_url, values)) == [
            ("{warmup,reading_tap,conjugation,grammar,writing}",)
        ]
    finally:
        command.downgrade(config, "base")
        command.upgrade(config, "head")


def test_undoing_the_writing_migration_drops_the_writing_reviews(database_url: str) -> None:
    config = _alembic_config(database_url)
    sources = "SELECT source::text FROM review_log"
    values = "SELECT enum_range(NULL::review_source)::text"
    try:
        asyncio.run(
            _run(
                database_url,
                "INSERT INTO learner (id, telegram_user_id) VALUES (1, 1)",
                """
                INSERT INTO memory_card (learner_id, unit_kind, unit_key, knowledge_type, due)
                VALUES (1, 'word', '1', 'recall', now())
                """,
                "INSERT INTO review_log (card_id, rating, source, reviewed_at) "
                "SELECT id, 'good', 'writing'::review_source, now() FROM memory_card",
                "INSERT INTO review_log (card_id, rating, source, reviewed_at) "
                "SELECT id, 'good', 'warmup'::review_source, now() FROM memory_card",
            )
        )

        command.downgrade(config, "0008")
        assert asyncio.run(_run(database_url, sources)) == [("warmup",)]
        assert asyncio.run(_run(database_url, values)) == [
            ("{warmup,reading_tap,conjugation,grammar}",)
        ]

        command.upgrade(config, "head")
        assert asyncio.run(_run(database_url, values)) == [
            ("{warmup,reading_tap,conjugation,grammar,writing}",)
        ]
    finally:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
