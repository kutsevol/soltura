from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner
from soltura.srs.service import save_word
from tests.factories import LearnerFactory, LexemeFactory

SAVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
LATER = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
async def saved_words(session: AsyncSession, learner: Learner) -> None:
    other = LearnerFactory.build()
    nieto, aunque = (LexemeFactory.build(lemma=lemma) for lemma in ("nieto", "aunque"))
    session.add_all([other, nieto, aunque])
    await session.flush()
    assert learner.id is not None and other.id is not None
    assert nieto.id is not None and aunque.id is not None
    await save_word(session, learner.id, nieto.id, "Mi nieto juega.", LATER)
    await save_word(session, learner.id, aunque.id, "Aunque llueve, salimos.", SAVED_AT)
    await save_word(session, other.id, aunque.id, "Aunque no quiero, voy.", SAVED_AT)
