from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.community.postgres import PostgresContainer

from soltura.app import create_app
from soltura.db import get_session
from soltura.learner.models import Learner, Lexeme
from tests.factories import LearnerFactory, LexemeFactory
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
def llm() -> FakeLLM:
    return FakeLLM()
