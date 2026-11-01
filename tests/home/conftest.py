from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner, Lexeme
from soltura.srs.service import save_word

SAVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


@pytest.fixture
async def saved_word(session: AsyncSession, learner: Learner, lexemes: list[Lexeme]) -> None:
    assert learner.id is not None and lexemes[2].id is not None
    await save_word(session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", SAVED_AT)
