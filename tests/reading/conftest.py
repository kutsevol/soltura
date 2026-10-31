from collections.abc import Awaitable, Callable

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.nlp import analyze
from soltura.learner.models import Learner, LearnerLexeme, LexemeOrigin, LexemeStatus
from soltura.reading.service import GeneratedText
from tests.factories import LexemeFactory

EASY_TEXT = GeneratedText(
    title="Un día de sol", text="Hoy hace sol. Voy a la playa con mi hermano y comemos pan."
)
HARD_TEXT = GeneratedText(
    title="Un día de sol",
    text="Hoy hace sol. El arrendatario impugnó la fianza y el notario redactó un acta.",
)


KnowFn = Callable[[str], Awaitable[None]]


@pytest.fixture
def know(session: AsyncSession, learner: Learner) -> KnowFn:
    # Marks every lemma of a text as known to the learner, creating the lexemes.
    async def mark(text: str) -> None:
        assert learner.id is not None
        lemmas = sorted({token.lemma for token in analyze(text)})
        lexemes = [
            LexemeFactory.build(lemma=lemma, frequency_rank=5000 + i)
            for i, lemma in enumerate(lemmas)
        ]
        session.add_all(lexemes)
        await session.flush()
        session.add_all(
            LearnerLexeme(
                learner_id=learner.id,
                lexeme_id=lexeme.id,
                status=LexemeStatus.KNOWN,
                origin=LexemeOrigin.ONBOARDING,
            )
            for lexeme in lexemes
            if lexeme.id is not None
        )
        await session.flush()

    return mark
