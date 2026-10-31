import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner
from tests.factories import LearnerFactory


@pytest.fixture
async def other_learner(session: AsyncSession) -> Learner:
    learner = LearnerFactory.build()
    session.add(learner)
    await session.flush()
    return learner
