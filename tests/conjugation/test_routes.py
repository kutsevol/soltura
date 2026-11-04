import re

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from soltura.learner.models import Lexeme, ReviewLog, ReviewSource

SER_PRESENT = ["soy", "eres", "es", "somos", "sois", "son"]


def _hidden(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, f"no hidden field {name}"
    return match.group(1).replace("&#34;", '"').replace("&quot;", '"').replace("&amp;", "&")


async def _answer(client: AsyncClient, page: str, answer: str, give_up: bool = False) -> str:
    data = {
        "card_id": _hidden(page, "card_id"),
        "queue": _hidden(page, "queue"),
        "started_at": _hidden(page, "started_at"),
        "answer": answer,
    }
    if give_up:
        data["give_up"] = "1"
    response = await client.post("/conjugation/answer", data=data)
    assert response.status_code == 200
    return response.text


async def _next(client: AsyncClient, result: str) -> str:
    response = await client.post("/conjugation/next", data={"queue": _hidden(result, "queue")})
    assert response.status_code == 200
    return response.text


async def test_a_session_goes_through_every_card_and_ends_on_the_done_screen(
    learner_client: AsyncClient, session: AsyncSession, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text
    assert "<strong>ser</strong>" in page and "yo …" in page and "Ще карток: 5" in page

    for index, form in enumerate(SER_PRESENT):
        result = await _answer(learner_client, page, form)
        assert "Правильно" in result
        page = await _next(learner_client, result)
        if index < len(SER_PRESENT) - 1:
            assert f"Ще карток: {len(SER_PRESENT) - index - 2}" in page

    assert "Сесію завершено" in page
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [log.answer for log in logs] == SER_PRESENT
    assert {log.source for log in logs} == {ReviewSource.CONJUGATION}


async def test_a_wrong_answer_shows_the_verdict_and_the_right_form(
    learner_client: AsyncClient, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text

    result = await _answer(learner_client, page, "eres")

    assert "Ще раз" in result
    assert "Ваша відповідь: eres" in result
    assert "Очікувалось: <strong>soy</strong>" in result
    assert "tú …" in await _next(learner_client, result)


async def test_giving_up_shows_the_right_form(
    learner_client: AsyncClient, verb_lexemes: list[Lexeme]
) -> None:
    page = (await learner_client.get("/conjugation")).text

    result = await _answer(learner_client, page, "soy", give_up=True)

    assert "Ще раз" in result
    assert "Очікувалось: <strong>soy</strong>" in result


async def test_a_learner_with_no_verbs_to_practise_sees_the_done_screen(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/conjugation")

    assert page.status_code == 200
    assert "Сесію завершено" in page.text


async def test_a_broken_session_state_is_refused(learner_client: AsyncClient) -> None:
    response = await learner_client.post("/conjugation/next", data={"queue": "not json"})

    assert response.status_code == 400
