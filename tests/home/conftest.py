from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner, Lexeme, PlacementRun
from soltura.learner.repository import save_placement_run
from soltura.srs.service import save_word

SAVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


@pytest.fixture
async def saved_word(session: AsyncSession, learner: Learner, lexemes: list[Lexeme]) -> None:
    assert learner.id is not None and lexemes[2].id is not None
    await save_word(session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", SAVED_AT)


BANDS = [{"band": 0, "max_rank": 250, "correct": 5, "total": 5}]


@pytest.fixture
async def placement_run(session: AsyncSession, learner: Learner) -> PlacementRun:
    assert learner.id is not None
    return await save_placement_run(session, learner.id, 500, BANDS)


@pytest.fixture
async def failed_placement_run(session: AsyncSession, learner: Learner) -> PlacementRun:
    assert learner.id is not None
    return await save_placement_run(session, learner.id, 0, BANDS)
