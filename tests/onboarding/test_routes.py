import re

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from soltura.learner.models import Learner, LearnerLexeme, Lexeme, LexemeStatus
from soltura.onboarding.service import PlacementSentence, PlacementSentences
from tests.onboarding.conftest import CORRECT, JudgeByAnswer


def _hidden(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, f"no hidden field {name}"
    return match.group(1).replace("&#34;", '"').replace("&quot;", '"').replace("&amp;", "&")


async def test_the_intro_explains_the_test(onboarding_client: AsyncClient) -> None:
    response = await onboarding_client.get("/onboarding")

    assert response.status_code == 200
    assert "40" in response.text
    assert 'hx-post="/onboarding/start"' in response.text


async def test_a_full_placement_marks_the_passed_bands_known(
    onboarding_client: AsyncClient,
    session: AsyncSession,
    learner: Learner,
    banded_lexemes: list[Lexeme],
    judge: JudgeByAnswer,
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    judge.answer(
        PlacementSentences(
            sentences=[
                PlacementSentence(lemma=lemma, sentence=f"Hoy veo {lemma}.", target_form=lemma)
                for lemma in nouns
            ]
        )
    )
    card = await onboarding_client.post("/onboarding/start")
    assert "Слово 1 з 40" in card.text

    for _ in range(40):
        mark = re.search(r"<mark>(word(\d)x\d)</mark>", card.text)
        assert mark, card.text
        band = int(mark.group(2))
        card = await onboarding_client.post(
            "/onboarding/answer",
            data={
                "queue": _hidden(card.text, "queue"),
                "answered": _hidden(card.text, "answered"),
                "answer": CORRECT if band < 3 else "не знаю",
            },
        )

    assert "Знайомими позначено 1000 найчастотніших слів" in card.text
    known = (
        await session.execute(
            select(func.count()).where(
                col(LearnerLexeme.learner_id) == learner.id,
                col(LearnerLexeme.status) == LexemeStatus.KNOWN,
            )
        )
    ).scalar_one()
    assert known == sum(1 for lexeme in banded_lexemes if lexeme.frequency_rank <= 1000)


async def test_an_empty_dictionary_asks_to_seed_it(onboarding_client: AsyncClient) -> None:
    response = await onboarding_client.post("/onboarding/start")

    assert response.status_code == 409
    assert "make seed-lexemes" in response.text
