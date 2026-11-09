from httpx import AsyncClient

from soltura.reading.topics import TOPICS
from soltura.writing.service import Correction
from tests.conftest import EASY_TEXT, KnowFn
from tests.fakes import FakeLLM

TOPIC = TOPICS[0].label
BUTTON = 'action="/study/next"'
TEXT = "Yo soy cansado porque trabajo mucho."


async def _session_on(client: AsyncClient, step: str) -> None:
    await client.post("/study/start", data={"topic": TOPIC})
    steps = ["warmup", "reading", "grammar", "writing"]
    for earlier in steps[: steps.index(step)]:
        await client.post("/study/next", data={"step": earlier})


async def test_the_warm_up_offers_the_next_step_when_nothing_is_due(
    learner_client: AsyncClient,
) -> None:
    await _session_on(learner_client, "warmup")

    page = await learner_client.get("/warmup")

    assert BUTTON in page.text
    assert 'name="step" value="warmup"' in page.text


async def test_the_warm_up_offers_the_next_step_after_the_last_card(
    learner_client: AsyncClient,
) -> None:
    await _session_on(learner_client, "warmup")

    response = await learner_client.post("/warmup/next", data={"queue": "[]"})

    assert 'name="step" value="warmup"' in response.text


async def test_no_screen_offers_the_next_step_without_a_session(
    learner_client: AsyncClient,
) -> None:
    warmup = await learner_client.get("/warmup")
    grammar = await learner_client.post("/grammar/next", data={"queue": "[]"})

    assert BUTTON not in warmup.text + grammar.text


async def test_a_module_does_not_offer_the_next_step_while_the_session_is_elsewhere(
    learner_client: AsyncClient,
) -> None:
    await _session_on(learner_client, "reading")

    warmup = await learner_client.get("/warmup")
    grammar = await learner_client.post("/grammar/next", data={"queue": "[]"})

    assert BUTTON not in warmup.text + grammar.text


async def test_grammar_offers_the_next_step_when_the_practice_is_done(
    learner_client: AsyncClient,
) -> None:
    await _session_on(learner_client, "grammar")

    response = await learner_client.post("/grammar/next", data={"queue": "[]"})

    assert 'name="step" value="grammar"' in response.text


async def test_reading_offers_the_next_step_under_the_text(
    learner_client: AsyncClient, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)
    await _session_on(learner_client, "reading")

    response = await learner_client.post("/reading/text", data={"topic": "la playa"})

    assert 'name="step" value="reading"' in response.text


async def test_the_journal_offers_the_next_step_under_the_result(
    learner_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[]))
    await _session_on(learner_client, "writing")

    response = await learner_client.post("/journal", data={"text": TEXT})

    assert 'name="step" value="writing"' in response.text


async def test_pressing_the_button_in_a_walk_moves_on_to_the_next_screen(
    learner_client: AsyncClient,
) -> None:
    await _session_on(learner_client, "warmup")

    moved = await learner_client.post("/study/next", data={"step": "warmup"})
    reading = await learner_client.get(moved.headers["location"])

    assert reading.status_code == 200
    assert 'hx-trigger="load"' in reading.text
