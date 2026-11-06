from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.grammar.service import GrammarItem
from soltura.grammar.units import get_unit
from soltura.grammar.views import card_view, lesson_view, progress_view, result_view
from soltura.learner.dependencies import LearnerIdDep
from soltura.templating import templates
from soltura.use_cases.grammar import (
    GrammarState,
    answer_exercise,
    grammar_progress,
    grammar_state,
    next_lesson,
    start_unit,
)
from soltura.web import answer_duration_ms, now_ms, parse_state

router = APIRouter(prefix="/grammar")

SessionDep = Annotated[AsyncSession, Depends(get_session)]

QUEUE = TypeAdapter(list[GrammarItem])
STATE_ERROR = "Bad grammar state"


def _card_context(item: GrammarItem, queue: list[GrammarItem]) -> dict[str, Any]:
    return {
        "card": card_view(item, len(queue)),
        "queue_json": QUEUE.dump_json(queue).decode(),
        "started_at": now_ms(),
    }


def _state_context(state: GrammarState) -> tuple[str, dict[str, Any]]:
    if state.items:
        first, *queue = state.items
        return "grammar/card.html", _card_context(first, queue)
    if state.lesson is not None:
        return "grammar/lesson.html", {"lesson": lesson_view(state.lesson)}
    return "grammar/done.html", {"lesson": None}


def _page(request: Request, state: GrammarState) -> HTMLResponse:
    fragment, context = _state_context(state)
    return templates.TemplateResponse(request, "grammar.html", {"fragment": fragment, **context})


@router.get("", response_class=HTMLResponse)
async def grammar_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    return _page(request, await grammar_state(session, learner_id, datetime.now(UTC)))


@router.get("/progress", response_class=HTMLResponse)
async def progress_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    progress = await grammar_progress(session, learner_id)
    return templates.TemplateResponse(
        request,
        "grammar/progress.html",
        {"progress": progress_view(progress, datetime.now(UTC))},
    )


@router.get("/units/{unit_id}", response_class=HTMLResponse)
async def lesson_page(request: Request, unit_id: str) -> HTMLResponse:
    unit = get_unit(unit_id)
    if unit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return _page(request, GrammarState(items=[], lesson=unit))


@router.post("/start", response_class=HTMLResponse)
async def start(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    unit_id: Annotated[str, Form()],
) -> HTMLResponse:
    now = datetime.now(UTC)
    try:
        await start_unit(session, learner_id, unit_id, now)
    except LookupError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from error
    fragment, context = _state_context(await grammar_state(session, learner_id, now))
    return templates.TemplateResponse(request, fragment, context)


@router.post("/answer", response_class=HTMLResponse)
async def answer(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    card_id: Annotated[int, Form()],
    queue: Annotated[str, Form()],
    started_at: Annotated[int, Form()],
    answer: Annotated[str, Form()] = "",
    give_up: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    if give_up:
        answer = ""
    parse_state(QUEUE, queue, STATE_ERROR)
    duration_ms = answer_duration_ms(started_at, now_ms())
    try:
        result = await answer_exercise(
            session, learner_id, card_id, answer, duration_ms, datetime.now(UTC)
        )
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from error
    return templates.TemplateResponse(
        request,
        "grammar/result.html",
        {"result": result_view(result, answer), "queue_json": queue},
    )


@router.post("/next", response_class=HTMLResponse)
async def next_card(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    queue: Annotated[str, Form()],
) -> HTMLResponse:
    items = parse_state(QUEUE, queue, STATE_ERROR)
    if not items:
        lesson = await next_lesson(session, learner_id)
        return templates.TemplateResponse(
            request,
            "grammar/done.html",
            {"lesson": lesson_view(lesson) if lesson is not None else None},
        )
    first, *rest = items
    return templates.TemplateResponse(request, "grammar/card.html", _card_context(first, rest))
