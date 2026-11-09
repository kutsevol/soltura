from urllib.parse import quote

from httpx import AsyncClient

from soltura.reading.topics import TOPICS

TOPIC = TOPICS[0].label
READING = f"/reading?topic={quote(TOPIC, safe='')}"


async def _start(client: AsyncClient) -> None:
    await client.post("/study/start", data={"topic": TOPIC})


async def test_without_a_session_the_page_offers_every_topic(learner_client: AsyncClient) -> None:
    page = await learner_client.get("/study")

    assert page.status_code == 200
    assert 'action="/study/start"' in page.text
    assert all(f'value="{topic.label}"' in page.text for topic in TOPICS)
    assert "aria-current" not in page.text


async def test_starting_a_session_lands_on_the_warm_up(learner_client: AsyncClient) -> None:
    response = await learner_client.post("/study/start", data={"topic": TOPIC})

    assert (response.status_code, response.headers["location"]) == (303, "/warmup")


async def test_a_topic_that_is_not_offered_is_refused(learner_client: AsyncClient) -> None:
    response = await learner_client.post("/study/start", data={"topic": "forged topic"})

    assert response.status_code == 400
    assert 'action="/study/start"' in (await learner_client.get("/study")).text


async def test_an_open_session_shows_the_steps_and_marks_the_current_one(
    learner_client: AsyncClient,
) -> None:
    await _start(learner_client)

    page = await learner_client.get("/study")

    assert TOPIC in page.text
    assert [step in page.text for step in ("Розминка", "Читання", "Граматика", "Письмо")] == [
        True
    ] * 4
    assert '<li class="current" aria-current="step">' in page.text
    assert 'href="/warmup" role="button">Відкрити' in page.text
    assert 'name="step" value="warmup"' in page.text


async def test_skipping_moves_to_the_next_step_and_opens_its_screen(
    learner_client: AsyncClient,
) -> None:
    await _start(learner_client)

    response = await learner_client.post("/study/next", data={"step": "warmup"})

    assert (response.status_code, response.headers["location"]) == (303, READING)
    page = await learner_client.get("/study")
    assert '<li class="done">' in page.text
    assert f'href="{READING}" role="button">Відкрити' in page.text


async def test_a_second_tap_on_the_same_step_does_not_skip_another(
    learner_client: AsyncClient,
) -> None:
    await _start(learner_client)

    await learner_client.post("/study/next", data={"step": "warmup"})
    again = await learner_client.post("/study/next", data={"step": "warmup"})

    assert again.headers["location"] == READING


async def test_leaving_the_last_step_ends_the_session(learner_client: AsyncClient) -> None:
    await _start(learner_client)
    for step in ("warmup", "reading", "grammar"):
        await learner_client.post("/study/next", data={"step": step})

    response = await learner_client.post("/study/next", data={"step": "writing"})

    assert response.headers["location"] == "/study"
    assert 'action="/study/start"' in (await learner_client.get("/study")).text


async def test_moving_on_without_a_session_leads_back_to_the_session_page(
    learner_client: AsyncClient,
) -> None:
    response = await learner_client.post("/study/next", data={"step": "warmup"})

    assert (response.status_code, response.headers["location"]) == (303, "/study")


async def test_starting_another_session_replaces_the_one_that_was_open(
    learner_client: AsyncClient,
) -> None:
    await _start(learner_client)
    await learner_client.post("/study/next", data={"step": "warmup"})

    await learner_client.post("/study/start", data={"topic": TOPICS[1].label})

    page = await learner_client.get("/study")
    assert TOPICS[1].label in page.text
    assert 'href="/warmup" role="button">Відкрити' in page.text


async def test_a_step_that_does_not_exist_is_refused(learner_client: AsyncClient) -> None:
    response = await learner_client.post("/study/next", data={"step": "dinner"})

    assert response.status_code == 422
