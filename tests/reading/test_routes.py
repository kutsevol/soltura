import json
import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.app import create_app
from soltura.config import settings
from soltura.db import get_session
from soltura.learner.models import Learner, Lexeme, MemoryCard, ReadingText, ReviewLog
from soltura.llm.client import LLMClient, get_llm
from soltura.reading.service import (
    MAX_GIST_ANSWER,
    MAX_GIST_TEXT,
    GeneratedText,
    GistVerdict,
    Gloss,
)
from soltura.reading.topics import TOPICS
from tests.conftest import EASY_TEXT, KnowFn
from tests.fakes import FakeLLM


async def test_the_reading_page_renders(reading_client: AsyncClient) -> None:
    response = await reading_client.get("/reading")

    assert response.status_code == 200
    assert 'hx-post="/reading/text"' in response.text


async def test_a_topic_label_in_the_address_starts_the_text_for_that_topic(
    reading_client: AsyncClient,
) -> None:
    response = await reading_client.get("/reading", params={"topic": TOPICS[1].label})

    assert 'hx-trigger="load"' in response.text
    assert json.dumps({"topic": TOPICS[1].prompt}) in response.text.replace("&#34;", '"')


@pytest.mark.parametrize("params", [{}, {"topic": "forged topic"}])
async def test_without_a_known_topic_in_the_address_no_text_starts_by_itself(
    reading_client: AsyncClient, params: dict[str, str]
) -> None:
    response = await reading_client.get("/reading", params=params)

    assert 'hx-trigger="load"' not in response.text


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


async def test_a_text_offers_the_gist_box(
    reading_client: AsyncClient, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    response = await reading_client.post("/reading/text", data={"topic": "la playa"})

    assert 'hx-post="/reading/gist"' in response.text
    assert f'name="text" value="{EASY_TEXT.text}"' in response.text


async def test_a_gist_answer_comes_back_with_a_verdict_and_a_reason(
    reading_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(GistVerdict(verdict="understood", reason="Текст про день на пляжі."))

    response = await reading_client.post(
        "/reading/gist", data={"text": EASY_TEXT.text, "answer": "Про день на пляжі"}
    )

    assert response.status_code == 200
    assert "Ви зрозуміли текст" in response.text
    assert "Текст про день на пляжі." in response.text


async def test_a_gist_verdict_stores_nothing(
    reading_client: AsyncClient, llm: FakeLLM, session: AsyncSession
) -> None:
    llm.answer(GistVerdict(verdict="missed", reason="Текст про пляж."))

    await reading_client.post("/reading/gist", data={"text": EASY_TEXT.text, "answer": "Про ліс"})

    for table in (MemoryCard, ReviewLog, ReadingText):
        assert (await session.execute(select(table))).scalars().all() == []


@pytest.mark.parametrize(
    "data",
    [
        {"text": EASY_TEXT.text, "answer": "  "},
        {"text": EASY_TEXT.text},
        {"text": "a" * (MAX_GIST_TEXT + 1), "answer": "Про сонце"},
        {"text": EASY_TEXT.text, "answer": "a" * (MAX_GIST_ANSWER + 1)},
    ],
    ids=["blank", "missing", "long text", "long answer"],
)
async def test_a_gist_request_that_is_empty_or_too_long_is_refused_before_the_model(
    reading_client: AsyncClient, llm: FakeLLM, data: dict[str, str]
) -> None:
    response = await reading_client.post("/reading/gist", data=data)

    assert response.status_code == 422
    assert llm.prompts == []


@pytest.mark.parametrize(
    "data",
    [
        {"text": EASY_TEXT.text, "answer": "  "},
        {"text": "a" * (MAX_GIST_TEXT + 1), "answer": "Про сонце"},
        {"text": EASY_TEXT.text, "answer": "a" * (MAX_GIST_ANSWER + 1)},
    ],
    ids=["blank", "long text", "long answer"],
)
async def test_a_refused_gist_request_is_answered_with_the_message_not_a_json_body(
    reading_client: AsyncClient, data: dict[str, str]
) -> None:
    response = await reading_client.post("/reading/gist", data=data)

    assert response.headers["content-type"].startswith("text/html")


async def test_the_gist_limits_are_inclusive(reading_client: AsyncClient, llm: FakeLLM) -> None:
    llm.answer(GistVerdict(verdict="understood", reason="Так."))

    response = await reading_client.post(
        "/reading/gist", data={"text": "a" * MAX_GIST_TEXT, "answer": "b" * MAX_GIST_ANSWER}
    )

    assert response.status_code == 200


async def test_a_newline_in_the_gist_answer_counts_once(
    reading_client: AsyncClient, llm: FakeLLM
) -> None:
    llm.answer(GistVerdict(verdict="understood", reason="Так."))
    answer = "\r\n".join(["b" * 9] * (MAX_GIST_ANSWER // 10))

    response = await reading_client.post(
        "/reading/gist", data={"text": EASY_TEXT.text, "answer": answer}
    )

    assert response.status_code == 200


async def test_the_gist_check_needs_a_learner(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", None)

    response = await client.post("/reading/gist", data={"text": "Hola", "answer": "Привіт"})

    assert response.status_code == 401


async def test_the_models_reason_and_the_text_are_escaped_on_the_page(
    reading_client: AsyncClient, llm: FakeLLM, know: KnowFn
) -> None:
    llm.answer(GistVerdict(verdict="partly", reason="<script>alert(1)</script>"))

    verdict = await reading_client.post(
        "/reading/gist", data={"text": EASY_TEXT.text, "answer": "Про сонце"}
    )

    assert "<script>" not in verdict.text
    assert "&lt;script&gt;" in verdict.text


async def test_a_text_with_quotes_does_not_break_out_of_the_hidden_field(
    reading_client: AsyncClient, llm: FakeLLM, know: KnowFn
) -> None:
    quoted = GeneratedText(title="Un día", text='Hoy hace sol. Dice "hola" & <b>sonríe</b>.')
    await know(f"{quoted.title}. {quoted.text}")
    llm.answer(quoted)

    response = await reading_client.post("/reading/text", data={"topic": "la playa"})

    assert (
        'name="text" value="Hoy hace sol. Dice &#34;hola&#34; &amp; &lt;b&gt;sonríe&lt;/b&gt;."'
        in response.text
    )
