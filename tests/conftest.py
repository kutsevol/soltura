from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.community.postgres import PostgresContainer

from soltura.app import create_app
from soltura.config import settings
from soltura.db import get_session
from soltura.learner.models import (
    KnowledgeType,
    Learner,
    Lexeme,
    LexemeOrigin,
    LexemeStatus,
    MemoryCard,
    UnitKind,
)
from soltura.llm.client import get_llm
from soltura.reading.service import UNRANKED
from soltura.srs.service import save_word
from tests.factories import (
    LearnerFactory,
    LearnerLexemeFactory,
    LexemeFactory,
    MemoryCardFactory,
)
from tests.fakes import FakeLLM

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as postgres:
        url = postgres.get_connection_url()
        alembic_config = Config(ROOT / "alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", url)
        command.upgrade(alembic_config, "head")
        yield url


@pytest.fixture
async def session(database_url: str) -> AsyncIterator[AsyncSession]:
    # Each test runs inside one outer transaction that is rolled back on teardown;
    # commits in the code under test become savepoints, so no test sees another's rows.
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def learner_client(
    session: AsyncSession, learner: Learner, llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", learner.telegram_user_id)
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_llm] = lambda: llm
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def learner(session: AsyncSession) -> Learner:
    learner = LearnerFactory.build()
    session.add(learner)
    await session.flush()
    return learner


@pytest.fixture
async def lexemes(session: AsyncSession) -> list[Lexeme]:
    lexemes = [
        LexemeFactory.build(lemma=lemma, frequency_rank=rank)
        for rank, lemma in enumerate(["ser", "estar", "aunque"], start=1)
    ]
    session.add_all(lexemes)
    await session.flush()
    return lexemes


@pytest.fixture
async def vocabulary_lexemes(session: AsyncSession) -> dict[str, Lexeme]:
    ranks = {
        "known": (10, "VERB"),
        "learning": (20, "NOUN"),
        "unmet": (30, "ADJ"),
        "name": (40, "PROPN"),
        "second_band": (300, "NOUN"),
        "tail": (9_000, "NOUN"),
        "unranked": (UNRANKED, "X"),
    }
    lexemes = {
        lemma: LexemeFactory.build(lemma=lemma, pos=pos, frequency_rank=rank)
        for lemma, (rank, pos) in ranks.items()
    }
    session.add_all(lexemes.values())
    await session.flush()
    return lexemes


@pytest.fixture
async def vocabulary_words(
    session: AsyncSession, learner: Learner, vocabulary_lexemes: dict[str, Lexeme]
) -> None:
    other = LearnerFactory.build()
    session.add(other)
    await session.flush()
    assert learner.id is not None and other.id is not None
    owned = [
        (learner.id, "known", LexemeStatus.KNOWN),
        (learner.id, "learning", LexemeStatus.LEARNING),
        (learner.id, "name", LexemeStatus.KNOWN),
        (learner.id, "second_band", LexemeStatus.KNOWN),
        (learner.id, "unranked", LexemeStatus.LEARNING),
        (other.id, "unmet", LexemeStatus.KNOWN),
    ]
    session.add_all(
        LearnerLexemeFactory.build(
            learner_id=learner_id,
            lexeme_id=vocabulary_lexemes[lemma].id,
            status=status,
            origin=LexemeOrigin.READING,
        )
        for learner_id, lemma, status in owned
    )
    await session.flush()


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
async def due_conjugation_card(session: AsyncSession, learner: Learner) -> MemoryCard:
    # Due long before any test's clock, and without a lexeme: the shape every
    # non-word card has.
    card = MemoryCardFactory.build(
        learner_id=learner.id,
        unit_kind=UnitKind.CONJUGATION,
        unit_key="tener|preterite|ellos",
        lexeme_id=None,
        knowledge_type=KnowledgeType.RECALL,
        due=datetime(2020, 1, 1, tzinfo=UTC),
    )
    session.add(card)
    await session.flush()
    return card


@pytest.fixture
async def verb_lexemes(session: AsyncSession) -> list[Lexeme]:
    # Everything ahead of ser that must not be offered: a noun, haber, a verb verbecc has
    # no template for and a weather verb. tener follows ser.
    ranked = [
        ("casa", "NOUN"),
        ("haber", "AUX"),
        ("zzzar", "VERB"),
        ("llover", "VERB"),
        ("ser", "AUX"),
        ("tener", "VERB"),
    ]
    lexemes = [
        LexemeFactory.build(lemma=lemma, pos=pos, frequency_rank=rank)
        for rank, (lemma, pos) in enumerate(ranked, start=1)
    ]
    session.add_all(lexemes)
    await session.flush()
    return lexemes


WARMUP_SAVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


@pytest.fixture
async def saved_aunque(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> dict[KnowledgeType, MemoryCard]:
    assert learner.id is not None and lexemes[2].id is not None
    cards = await save_word(
        session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", WARMUP_SAVED_AT
    )
    return {card.knowledge_type: card for card in cards}
