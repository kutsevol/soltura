import re

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from soltura.learner.models import KnowledgeType, MemoryCard, ReviewLog, ReviewSource
from soltura.practice.checking import TranslationVerdict
from tests.fakes import FakeLLM
from tests.warmup.test_service import RECALL_CONTEXT, RECOGNIZE_CONTEXT


def _hidden(html: str, name: str) -> str:
    match = re.search(rf'name="{name}" value="([^"]*)"', html)
    assert match, f"no hidden field {name}"
    return (
        match.group(1)
        .replace("&#34;", '"')
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&amp;", "&")
    )


async def test_the_index_opens_the_warmup_when_cards_are_due(
    warmup_client: AsyncClient, saved_aunque: dict[KnowledgeType, MemoryCard]
) -> None:
    response = await warmup_client.get("/")

    assert (response.status_code, response.headers["location"]) == (303, "/warmup")


async def test_the_index_opens_reading_when_nothing_is_due(warmup_client: AsyncClient) -> None:
    response = await warmup_client.get("/")

    assert (response.status_code, response.headers["location"]) == (303, "/reading")


async def test_a_session_goes_through_every_card_and_on_to_reading(
    warmup_client: AsyncClient,
    session: AsyncSession,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
) -> None:
    llm.answer(RECOGNIZE_CONTEXT, RECALL_CONTEXT)
    llm.answer(TranslationVerdict(verdict="correct", reason="Так.", expected="хоча"))

    page = await warmup_client.get("/warmup")
    assert "_____" in page.text and RECALL_CONTEXT.translation in page.text

    first = await warmup_client.post(
        "/warmup/answer",
        data={
            "item": _hidden(page.text, "item"),
            "queue": _hidden(page.text, "queue"),
            "started_at": _hidden(page.text, "started_at"),
            "answer": "aunque",
        },
    )
    assert "Правильно" in first.text

    second_card = await warmup_client.post(
        "/warmup/next", data={"queue": _hidden(first.text, "queue")}
    )
    assert "<mark>aunque</mark>" in second_card.text

    second = await warmup_client.post(
        "/warmup/answer",
        data={
            "item": _hidden(second_card.text, "item"),
            "queue": _hidden(second_card.text, "queue"),
            "started_at": _hidden(second_card.text, "started_at"),
            "answer": "хоча",
        },
    )
    assert "Правильно" in second.text
    done = await warmup_client.post("/warmup/next", data={"queue": _hidden(second.text, "queue")})

    assert 'href="/reading"' in done.text
    sources = (await session.execute(select(ReviewLog.source))).scalars().all()
    assert sources == [ReviewSource.WARMUP, ReviewSource.WARMUP]


async def test_giving_up_ignores_whatever_was_typed(
    warmup_client: AsyncClient, saved_aunque: dict[KnowledgeType, MemoryCard], llm: FakeLLM
) -> None:
    llm.answer(RECOGNIZE_CONTEXT, RECALL_CONTEXT)
    page = await warmup_client.get("/warmup")

    response = await warmup_client.post(
        "/warmup/answer",
        data={
            "item": _hidden(page.text, "item"),
            "queue": _hidden(page.text, "queue"),
            "started_at": _hidden(page.text, "started_at"),
            "answer": "aunque",
            "give_up": "1",
        },
    )

    assert "Ще раз" in response.text


async def test_a_tampered_queue_is_rejected(warmup_client: AsyncClient) -> None:
    response = await warmup_client.post("/warmup/next", data={"queue": "not json"})

    assert response.status_code == 400
