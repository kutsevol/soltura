from typing import cast

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Lexeme
from soltura.llm.client import Effort, SchemaT
from soltura.onboarding.service import BANDS
from soltura.practice.checking import TranslationVerdict
from tests.factories import LexemeFactory
from tests.fakes import FakeLLM

CORRECT = "так"


class JudgeByAnswer(FakeLLM):
    # Judges a translation as correct when the learner typed CORRECT, so concurrent
    # judging needs no particular call order.
    async def __call__(
        self,
        schema: type[SchemaT],
        system: str,
        prompt: str,
        effort: Effort,
        max_tokens: int = 16_000,
    ) -> SchemaT:
        if schema is TranslationVerdict:
            self.prompts.append(prompt)
            verdict = "correct" if prompt.endswith(f"Learner's answer: {CORRECT}") else "wrong"
            return cast(SchemaT, TranslationVerdict(verdict=verdict, reason="", expected=""))
        return await super().__call__(schema, system, prompt, effort, max_tokens)


@pytest.fixture
def judge() -> JudgeByAnswer:
    return JudgeByAnswer()


@pytest.fixture
async def banded_lexemes(session: AsyncSession) -> list[Lexeme]:
    # Five nouns at the top of every band, plus a preposition per band that the
    # placement must never pick.
    lexemes = [
        LexemeFactory.build(lemma=f"word{band}x{i}", pos="NOUN", frequency_rank=max_rank - i)
        for band, (_, max_rank) in enumerate(BANDS)
        for i in range(5)
    ] + [
        LexemeFactory.build(lemma=f"prep{band}", pos="ADP", frequency_rank=min_rank)
        for band, (min_rank, _) in enumerate(BANDS)
    ]
    session.add_all(lexemes)
    await session.flush()
    return lexemes
