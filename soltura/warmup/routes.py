from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerIdDep
from soltura.learner.models import Rating
from soltura.llm.client import LLMClient, get_llm
from soltura.practice.text import split_around
from soltura.templating import templates
from soltura.warmup.service import WarmupItem, answer_item, build_warmup
from soltura.web import answer_duration_ms, now_ms, parse_state

router = APIRouter(prefix="/warmup")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]

ITEM = TypeAdapter(WarmupItem)
QUEUE = TypeAdapter(list[WarmupItem])
STATE_ERROR = "Bad warm-up state"

RATING_LABEL = {
    Rating.GOOD: "Правильно",
    Rating.EASY: "Легко",
    Rating.HARD: "Майже",
    Rating.AGAIN: "Ще раз",
}


def _card_context(item: WarmupItem, queue: list[WarmupItem]) -> dict[str, Any]:
    before, target, after = split_around(item.sentence, item.target_form) or (
        item.sentence,
        "",
        "",
    )
    return {
        "item": item,
        "item_json": ITEM.dump_json(item).decode(),
        "queue_json": QUEUE.dump_json(queue).decode(),
        "remaining": len(queue),
        "before": before,
        "target": target,
        "after": after,
        "started_at": now_ms(),
    }


@router.get("", response_class=HTMLResponse)
async def warmup_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep, llm: LLMDep
) -> HTMLResponse:
    items = await build_warmup(session, llm, learner_id, datetime.now(UTC))
    if not items:
        return templates.TemplateResponse(request, "warmup.html", {"empty": True})
    first, *queue = items
    return templates.TemplateResponse(
        request, "warmup.html", {"empty": False, **_card_context(first, queue)}
    )


@router.post("/answer", response_class=HTMLResponse)
async def answer(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    item: Annotated[str, Form()],
    queue: Annotated[str, Form()],
    started_at: Annotated[int, Form()],
    answer: Annotated[str, Form()] = "",
    give_up: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    if give_up:
        answer = ""
    current = parse_state(ITEM, item, STATE_ERROR)
    parse_state(QUEUE, queue, STATE_ERROR)
    duration_ms = answer_duration_ms(started_at, now_ms())
    try:
        result = await answer_item(
            session, llm, learner_id, current, answer, duration_ms, datetime.now(UTC)
        )
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from error
    return templates.TemplateResponse(
        request,
        "warmup/result.html",
        {
            "result": result,
            "label": RATING_LABEL[result.rating],
            "answer": answer.strip(),
            "item": current,
            "queue_json": queue,
        },
    )


@router.post("/next", response_class=HTMLResponse)
async def next_card(request: Request, queue: Annotated[str, Form()]) -> HTMLResponse:
    items = parse_state(QUEUE, queue, STATE_ERROR)
    if not items:
        return templates.TemplateResponse(request, "warmup/done.html")
    first, *rest = items
    return templates.TemplateResponse(request, "warmup/card.html", _card_context(first, rest))
