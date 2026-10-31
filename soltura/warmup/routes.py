import time
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import current_learner
from soltura.learner.models import Learner, Rating
from soltura.llm.client import LLMClient, get_llm
from soltura.templating import templates
from soltura.warmup.service import WarmupItem, answer_item, build_warmup

router = APIRouter(prefix="/warmup")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LearnerDep = Annotated[Learner, Depends(current_learner)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]

ITEM = TypeAdapter(WarmupItem)
QUEUE = TypeAdapter(list[WarmupItem])
MAX_DURATION_MS = 10 * 60 * 1000

RATING_LABEL = {
    Rating.GOOD: "Правильно",
    Rating.EASY: "Легко",
    Rating.HARD: "Майже",
    Rating.AGAIN: "Ще раз",
}


def _now_ms() -> int:
    return time.time_ns() // 1_000_000


def _split_around(sentence: str, form: str) -> tuple[str, str, str]:
    start = sentence.lower().find(form.lower())
    if start < 0:
        return sentence, "", ""
    end = start + len(form)
    return sentence[:start], sentence[start:end], sentence[end:]


def _card_context(item: WarmupItem, queue: list[WarmupItem]) -> dict[str, Any]:
    before, target, after = _split_around(item.sentence, item.target_form)
    return {
        "item": item,
        "item_json": ITEM.dump_json(item).decode(),
        "queue_json": QUEUE.dump_json(queue).decode(),
        "remaining": len(queue),
        "before": before,
        "target": target,
        "after": after,
        "started_at": _now_ms(),
    }


def _parse(adapter: TypeAdapter[Any], raw: str) -> Any:
    try:
        return adapter.validate_json(raw)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad warm-up state"
        ) from error


def _learner_id(learner: Learner) -> int:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    return learner.id


@router.get("", response_class=HTMLResponse)
async def warmup_page(
    request: Request, session: SessionDep, learner: LearnerDep, llm: LLMDep
) -> HTMLResponse:
    items = await build_warmup(session, llm, _learner_id(learner), datetime.now(UTC))
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
    learner: LearnerDep,
    llm: LLMDep,
    item: Annotated[str, Form()],
    queue: Annotated[str, Form()],
    started_at: Annotated[int, Form()],
    answer: Annotated[str, Form()] = "",
    give_up: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    if give_up:
        answer = ""
    current: WarmupItem = _parse(ITEM, item)
    _parse(QUEUE, queue)
    duration_ms = min(max(_now_ms() - started_at, 0), MAX_DURATION_MS)
    try:
        result = await answer_item(
            session, llm, _learner_id(learner), current, answer, duration_ms, datetime.now(UTC)
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
    items: list[WarmupItem] = _parse(QUEUE, queue)
    if not items:
        return templates.TemplateResponse(request, "warmup/done.html")
    first, *rest = items
    return templates.TemplateResponse(request, "warmup/card.html", _card_context(first, rest))
