from collections.abc import AsyncGenerator
from functools import cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from soltura.config import settings


@cache
def get_engine() -> AsyncEngine:
    return create_async_engine(settings.database.url, pool_pre_ping=True)


@cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with get_session_factory()() as session:
        yield session
