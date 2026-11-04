import re

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from soltura.learner.models import Learner, LearnerLexeme, Lexeme, LexemeStatus
from soltura.learner.repository import save_placement_run
from soltura.onboarding.service import PlacementSentence, PlacementSentences
from tests.onboarding.conftest import CORRECT, JudgeByAnswer


def _hidden(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, f"no hidden field {name}"
    return match.group(1).replace("&#34;", '"').replace("&quot;", '"').replace("&amp;", "&")


async def test_the_intro_explains_the_test(onboarding_client: AsyncClient) -> None:
    response = await onboarding_client.get("/onboarding")

    assert response.status_code == 200
    assert "до 64" in response.text
    assert 'hx-post="/onboarding/start"' in response.text


async def test_a_learner_who_fails_two_bands_in_a_row_is_not_asked_the_rest(
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
                PlacementSentence(
                    lemma=lemma,
                    sentence=f"Hoy veo {lemma}.",
                    target_form=lemma,
                    meaning=f"значення {lemma}",
                )
                for lemma in nouns
            ]
        )
    )
    card = await onboarding_client.post("/onboarding/start")
    assert "Слово 1 з 64" in card.text

    while "Знайомими" not in card.text:
        mark = re.search(r"<mark>(word(\d)x\d)</mark>", card.text)
        assert mark, card.text
        band = int(mark.group(2))
        card = await onboarding_client.post(
            "/onboarding/answer",
            data={
                "queue": _hidden(card.text, "queue"),
                "answered": _hidden(card.text, "answered"),
                "answer": CORRECT if band < 3 else "",
                "give_up": band >= 3,
            },
        )

    # Bands 3 and 4 are both at 0%, so the test ends after five bands of eight words.
    assert "Знайомими позначено 1000 найчастотніших слів" in card.text
    assert "до 2000" in card.text
    assert "до 3000" not in card.text
    known = (
        await session.execute(
            select(func.count()).where(
                col(LearnerLexeme.learner_id) == learner.id,
                col(LearnerLexeme.status) == LexemeStatus.KNOWN,
            )
        )
    ).scalar_one()
    assert known == sum(1 for lexeme in banded_lexemes if lexeme.frequency_rank <= 1000)

    page = await onboarding_client.get("/onboarding/result")

    assert page.status_code == 200
    assert "Знайомими позначено 1000 найчастотніших слів" in page.text
    assert "<td>до 250</td><td>8 з 8</td>" in page.text
    assert '<a href="/onboarding" role="button" class="outline">Пройти знову</a>' in page.text
    assert "Ваші відповіді (40)" in page.text
    assert page.text.count("✓ word") == 24
    assert page.text.count("✗ word") == 16
    # A skipped word is not judged, yet its meaning is still shown.
    assert page.text.count("значення word") == 16
    assert "Відповіді немає" not in page.text


async def test_an_empty_dictionary_asks_to_seed_it(onboarding_client: AsyncClient) -> None:
    response = await onboarding_client.post("/onboarding/start")

    assert response.status_code == 409
    assert "make seed-lexemes" in response.text


async def test_the_result_page_without_a_run_sends_the_learner_to_the_test(
    onboarding_client: AsyncClient,
) -> None:
    response = await onboarding_client.get("/onboarding/result")

    assert response.status_code == 303
    assert response.headers["location"] == "/onboarding"


async def test_a_run_saved_without_answers_still_shows_its_table(
    onboarding_client: AsyncClient, session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    bands = [{"band": 0, "max_rank": 250, "correct": 5, "total": 5}]
    await save_placement_run(session, learner.id, 250, bands)

    page = await onboarding_client.get("/onboarding/result")

    assert page.status_code == 200
    assert "<td>до 250</td><td>5 з 5</td>" in page.text
    assert "Ваші відповіді" not in page.text
