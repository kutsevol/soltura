import json
import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.app import create_app
from soltura.config import settings
from soltura.db import get_session
from soltura.learner.models import Learner, Lexeme
from soltura.llm.client import LLMClient, get_llm
from soltura.reading.service import Gloss
from soltura.reading.topics import TOPICS
from tests.fakes import FakeLLM
from tests.reading.conftest import EASY_TEXT, KnowFn


async def test_the_reading_page_renders(reading_client: AsyncClient) -> None:
    response = await reading_client.get("/reading")

    assert response.status_code == 200
    assert 'hx-post="/reading/text"' in response.text


async def test_a_new_text_comes_back_with_every_word_tappable(
    reading_client: AsyncClient, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    response = await reading_client.post("/reading/text", data={"topic": "la playa"})

    assert response.status_code == 200
    assert f"<h2>{EASY_TEXT.title}</h2>" in response.text
    assert response.text.count('class="word"') == 13
    assert '"sentence": "Hoy hace sol."' in response.text


async def test_a_request_without_topic_or_text_is_rejected(reading_client: AsyncClient) -> None:
    response = await reading_client.post("/reading/text", data={"topic": " "})

    assert response.status_code == 422
    assert "Вкажіть тему" in response.text


async def test_tapping_and_saving_a_word(
    reading_client: AsyncClient, llm: FakeLLM, lexemes: list[Lexeme]
) -> None:
    llm.answer(Gloss(lemma="ser", translation="бути"))

    tapped = await reading_client.post(
        "/reading/tap", data={"word": "fue", "sentence": "La película fue buena."}
    )
    saved = await reading_client.post(
        "/reading/save", data={"lemma": "ser", "sentence": "La película fue buena."}
    )

    assert tapped.status_code == 200
    assert "<em>ser</em>" in tapped.text
    assert '"lemma": "ser"' in tapped.text
    assert saved.status_code == 200
    assert "<strong>ser</strong>" in saved.text


async def test_a_missing_api_key_is_named_instead_of_failing(
    session: AsyncSession, learner: Learner, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", learner.telegram_user_id)
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_llm] = lambda: LLMClient(None, "claude-sonnet-5-5")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        missing_key = await client.post("/reading/text", data={"topic": "la playa"})
        no_topic = await client.post("/reading/text", data={"topic": ""})

    assert missing_key.status_code == 503
    assert "ANTHROPIC_API_KEY" in missing_key.text
    assert no_topic.status_code == 422


async def test_every_topic_button_generates_a_text_on_its_topic(
    reading_client: AsyncClient, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    page = await reading_client.get("/reading")
    buttons = re.findall(r"hx-vals='([^']*)'[^>]*>([^<]+)</button>", page.text)
    assert [label for _, label in buttons] == [topic.label for topic in TOPICS]

    for vals, _ in buttons:
        llm.answer(EASY_TEXT)
        topic = json.loads(vals)["topic"]

        response = await reading_client.post("/reading/text", data={"topic": topic})

        assert response.status_code == 200
        assert f"Topic: {topic}." in llm.prompts[-1]
