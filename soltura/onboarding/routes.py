from dataclasses import asdict
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerIdDep
from soltura.llm.client import LLMClient, get_llm
from soltura.onboarding.screens import latest_result_screen, result_screen
from soltura.onboarding.service import (
    BANDS,
    WORDS_PER_BAND,
    Finished,
    NothingToAnswer,
    PlacementItem,
    answer_word,
    build_placement,
    learn_from_result,
)
from soltura.onboarding.views import card_view, learn_view, result_view
from soltura.templating import templates
from soltura.web import parse_state

router = APIRouter(prefix="/onboarding")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]

ITEMS = TypeAdapter(list[PlacementItem])
STATE_ERROR = "Bad onboarding state"


def _card_context(queue: list[PlacementItem], answered: list[PlacementItem]) -> dict[str, Any]:
    return {
        **asdict(card_view(queue, answered)),
        "queue_json": ITEMS.dump_json(queue).decode(),
        "answered_json": ITEMS.dump_json(answered).decode(),
    }


@router.get("", response_class=HTMLResponse)
async def onboarding_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "onboarding.html", {"words": len(BANDS) * WORDS_PER_BAND, "bands": len(BANDS)}
    )


@router.get("/result", response_model=None)
async def result_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse | RedirectResponse:
    screen = await latest_result_screen(session, learner_id)
    if screen is None:
        return RedirectResponse("/onboarding", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request, "onboarding/result_page.html", vars(result_view(screen))
    )


@router.post("/learn", response_class=HTMLResponse)
async def learn(request: Request, session: SessionDep, learner_id: LearnerIdDep) -> HTMLResponse:
    outcome = await learn_from_result(session, learner_id, datetime.now(UTC))
    return templates.TemplateResponse(request, "onboarding/learn.html", vars(learn_view(outcome)))


@router.post("/start", response_class=HTMLResponse)
async def start(request: Request, session: SessionDep, llm: LLMDep) -> HTMLResponse:
    items = await build_placement(session, llm)
    if not items:
        return templates.TemplateResponse(
            request,
            "reading/error.html",
            {"message": "Словник порожній: спершу виконайте make seed-lexemes."},
            status_code=409,
        )
    return templates.TemplateResponse(request, "onboarding/card.html", _card_context(items, []))


@router.post("/answer", response_class=HTMLResponse)
async def answer(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    queue: Annotated[str, Form()],
    answered: Annotated[str, Form()],
    answer: Annotated[str, Form()] = "",
    give_up: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    remaining = parse_state(ITEMS, queue, STATE_ERROR)
    done = parse_state(ITEMS, answered, STATE_ERROR)
    try:
        step = await answer_word(session, llm, learner_id, remaining, done, answer, give_up)
    except NothingToAnswer as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to answer"
        ) from error
    if isinstance(step, Finished):
        screen = await result_screen(session, learner_id, step.result)
        return templates.TemplateResponse(
            request, "onboarding/result.html", vars(result_view(screen))
        )
    return templates.TemplateResponse(
        request, "onboarding/card.html", _card_context(step.queue, step.answered)
    )
