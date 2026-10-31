import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner, Lexeme
from tests.factories import LearnerFactory, LexemeFactory


@pytest.fixture
async def learner(session: AsyncSession) -> Learner:
    learner = LearnerFactory.build()
    session.add(learner)
    await session.flush()
    return learner


@pytest.fixture
async def other_learner(session: AsyncSession) -> Learner:
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
