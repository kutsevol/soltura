from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from soltura.language.seed import RankedLemma, rank_lemmas, save_lexemes, spanish_word_frequencies
from soltura.learner.models import Lexeme


def test_rank_lemmas_adds_up_the_frequencies_of_every_form() -> None:
    ranked = rank_lemmas({"es": 0.004, "son": 0.003, "casa": 0.002, "casas": 0.001})

    by_lemma = {item.lemma: item for item in ranked}
    assert [item.lemma for item in ranked] == ["ser", "casa"]
    assert by_lemma["ser"].frequency_rank == 1
    assert by_lemma["casa"].pos == "NOUN"


def test_rank_lemmas_puts_ser_in_the_top_ten_of_real_spanish() -> None:
    ranked = rank_lemmas(spanish_word_frequencies(2_000))

    assert "ser" in [item.lemma for item in ranked[:10]]


async def test_save_lexemes_updates_existing_lemmas_in_place(session: AsyncSession) -> None:
    await save_lexemes(session, [RankedLemma(lemma="casa", pos="NOUN", frequency_rank=200)])
    first = (await session.execute(select(Lexeme).where(Lexeme.lemma == "casa"))).scalar_one()
    first_id = first.id

    await save_lexemes(session, [RankedLemma(lemma="casa", pos="NOUN", frequency_rank=110)])
    session.expire_all()
    rows = (await session.execute(select(Lexeme).where(Lexeme.lemma == "casa"))).scalars().all()

    assert [(row.id, row.frequency_rank) for row in rows] == [(first_id, 110)]
