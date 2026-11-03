import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Lexeme
from tests.factories import LexemeFactory


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
