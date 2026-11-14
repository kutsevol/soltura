import re

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from soltura.grammar.units import all_units
from soltura.learner.models import ReviewLog, ReviewSource

FIRST = all_units()[0]


def _hidden(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, f"no hidden field {name}"
    return match.group(1).replace("&#34;", '"').replace("&quot;", '"').replace("&amp;", "&")


async def _start(client: AsyncClient, unit_id: str) -> str:
    response = await client.post("/grammar/start", data={"unit_id": unit_id})
    assert response.status_code == 200
    return response.text


async def _answer(client: AsyncClient, card: str, answer: str, give_up: bool = False) -> str:
    data = {
        "card_id": _hidden(card, "card_id"),
        "queue": _hidden(card, "queue"),
        "started_at": _hidden(card, "started_at"),
        "answer": answer,
    }
    if give_up:
        data["give_up"] = "1"
    response = await client.post("/grammar/answer", data=data)
    assert response.status_code == 200
    return response.text


async def _next(client: AsyncClient, result: str) -> str:
    response = await client.post("/grammar/next", data={"queue": _hidden(result, "queue")})
    assert response.status_code == 200
    return response.text


async def test_a_new_learner_sees_the_first_lesson_and_its_button_leads_to_the_first_exercise(
    learner_client: AsyncClient,
) -> None:
    page = await learner_client.get("/grammar")

    assert page.status_code == 200
    assert FIRST.title in page.text and FIRST.lesson.points[0] in page.text
    assert f"Рівень {FIRST.level}" in page.text and FIRST.level == "A1"
    assert FIRST.lesson.examples[0].spanish in page.text
    assert f'name="unit_id" value="{FIRST.id}"' in page.text

    card = await _start(learner_client, FIRST.id)

    assert "Ще вправ: 5" in card and FIRST.title in card


async def test_once_started_the_page_shows_the_exercises_and_not_the_lesson(
    learner_client: AsyncClient,
) -> None:
    await _start(learner_client, FIRST.id)

    page = await learner_client.get("/grammar")

    assert "Ще вправ: 5" in page.text
    assert 'name="unit_id"' not in page.text


async def test_a_session_goes_through_every_exercise_and_ends_by_offering_the_next_lesson(
    learner_client: AsyncClient, session: AsyncSession
) -> None:
    card = await _start(learner_client, FIRST.id)

    for index in range(len(FIRST.exercises)):
        result = await _answer(learner_client, card, "", give_up=True)
        assert "Ще раз" in result
        card = await _next(learner_client, result)
        if index < len(FIRST.exercises) - 1:
            assert f"Ще вправ: {len(FIRST.exercises) - index - 2}" in card

    assert "На зараз вправ для повторення немає" in card
    assert all_units()[1].title in card
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert len(logs) == len(FIRST.exercises)
    assert {log.source for log in logs} == {ReviewSource.GRAMMAR}


async def test_a_wrong_choice_shows_the_right_word_the_note_and_a_link_to_the_lesson(
    learner_client: AsyncClient,
) -> None:
    card = await _start(learner_client, "ser_estar")

    wrong = await _answer(learner_client, card, "xxx")

    assert "Ще раз" in wrong and "Ваша відповідь: xxx" in wrong
    assert re.search(r"Правильно: <strong>\S+</strong>", wrong)
    assert '<a href="/grammar/units/ser_estar">Правило</a>' in wrong


async def test_a_right_answer_still_shows_the_note(learner_client: AsyncClient) -> None:
    unit = next(unit for unit in all_units() if unit.id == "ser_estar")
    card = await _start(learner_client, unit.id)
    shown = re.search(r'class="sentence">([^<]*)<span', card)
    assert shown
    exercise = next(item for item in unit.exercises if item.sentence.startswith(shown.group(1)))

    result = await _answer(learner_client, card, exercise.answer)

    assert "Правильно" in result
    assert exercise.note in result


async def test_a_lesson_can_be_read_again_by_its_id(learner_client: AsyncClient) -> None:
    page = await learner_client.get("/grammar/units/por_para")

    assert page.status_code == 200
    assert "por чи para" in page.text


async def test_an_unknown_unit_is_not_found(learner_client: AsyncClient) -> None:
    assert (await learner_client.get("/grammar/units/nothing")).status_code == 404
    assert (
        await learner_client.post("/grammar/start", data={"unit_id": "nothing"})
    ).status_code == 404


async def test_a_card_that_is_not_the_learners_is_forbidden(learner_client: AsyncClient) -> None:
    response = await learner_client.post(
        "/grammar/answer",
        data={"card_id": 999999, "queue": "[]", "started_at": 0, "answer": "es"},
    )

    assert response.status_code == 403


async def test_a_broken_queue_is_a_bad_request(learner_client: AsyncClient) -> None:
    response = await learner_client.post("/grammar/next", data={"queue": "not json"})

    assert response.status_code == 400


async def test_the_progress_page_is_empty_for_a_new_learner(learner_client: AsyncClient) -> None:
    page = await learner_client.get("/grammar/progress")

    assert page.status_code == 200
    assert "Ще немає розпочатих правил" in page.text


async def test_the_progress_page_shows_a_started_unit_after_an_answer(
    learner_client: AsyncClient,
) -> None:
    card = await _start(learner_client, FIRST.id)
    await _answer(learner_client, card, "", give_up=True)

    page = await learner_client.get("/grammar/progress")

    assert f'<a href="/grammar/units/{FIRST.id}">{FIRST.title}</a>' in page.text
    assert "Відповідей: 1, правильних: 0%" in page.text
    assert f"У пам’яті: 0 з {len(FIRST.exercises)}" in page.text
    assert f"Ще не розпочато правил: {len(all_units()) - 1}" in page.text


async def test_the_grammar_page_links_to_the_progress(learner_client: AsyncClient) -> None:
    page = await learner_client.get("/grammar")

    assert '<a href="/grammar/progress">' in page.text
