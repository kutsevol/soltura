from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import current_learner
from soltura.learner.models import Learner
from soltura.llm.client import LLMClient, get_llm
from soltura.onboarding.service import (
    BANDS,
    LEARN_BATCH,
    WORDS_PER_BAND,
    PlacementItem,
    apply_placement,
    band_scores,
    build_placement,
    get_latest_placement,
    judge_items,
    learn_missed_words,
    missed_words,
    score_placement,
    should_stop,
)
from soltura.practice.text import split_around
from soltura.templating import templates

router = APIRouter(prefix="/onboarding")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LearnerDep = Annotated[Learner, Depends(current_learner)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]

ITEMS = TypeAdapter(list[PlacementItem])


def _parse(raw: str) -> list[PlacementItem]:
    try:
        return ITEMS.validate_json(raw)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad onboarding state"
        ) from error


def _card_context(queue: list[PlacementItem], answered: list[PlacementItem]) -> dict[str, Any]:
    current = queue[0]
    before, target, after = split_around(current.sentence, current.target_form) or (
        current.sentence,
        "",
        "",
    )
    return {
        "before": before,
        "target": target,
        "after": after,
        "queue_json": ITEMS.dump_json(queue).decode(),
        "answered_json": ITEMS.dump_json(answered).decode(),
        "position": len(answered) + 1,
        "total": len(answered) + len(queue),
        # The last word of a band is followed by a wait while its answers are judged.
        "checking": len(queue) == 1 or queue[1].band != current.band,
    }


async def _learn_context(session: AsyncSession, learner_id: int) -> dict[str, int]:
    missed = await missed_words(session, learner_id)
    return {"missed_total": len(missed), "missed_batch": min(len(missed), LEARN_BATCH)}


@router.get("", response_class=HTMLResponse)
async def onboarding_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "onboarding.html", {"words": len(BANDS) * WORDS_PER_BAND, "bands": len(BANDS)}
    )


@router.get("/result", response_model=None)
async def result_page(
    request: Request, session: SessionDep, learner: LearnerDep
) -> HTMLResponse | RedirectResponse:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    result = await get_latest_placement(session, learner.id)
    if result is None:
        return RedirectResponse("/onboarding", status_code=status.HTTP_303_SEE_OTHER)
    context = {"result": result, **await _learn_context(session, learner.id)}
    return templates.TemplateResponse(request, "onboarding/result_page.html", context)


@router.post("/learn", response_class=HTMLResponse)
async def learn(request: Request, session: SessionDep, learner: LearnerDep) -> HTMLResponse:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    added, _ = await learn_missed_words(session, learner.id, datetime.now(UTC))
    context = {"added": added, **await _learn_context(session, learner.id)}
    return templates.TemplateResponse(request, "onboarding/learn.html", context)


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
    learner: LearnerDep,
    llm: LLMDep,
    queue: Annotated[str, Form()],
    answered: Annotated[str, Form()],
    answer: Annotated[str, Form()] = "",
    give_up: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    remaining, done = _parse(queue), _parse(answered)
    if not remaining:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nothing to answer")
    current, *rest = remaining
    done.append(current.model_copy(update={"answer": "" if give_up else answer.strip()}))
    if not rest or rest[0].band != current.band:
        # A band is finished: judge it now, so a learner who has run out of known words
        # is not asked the rarer bands.
        done = await judge_items(llm, done)
        if rest and should_stop(band_scores(done)):
            rest = []
    if rest:
        return templates.TemplateResponse(
            request, "onboarding/card.html", _card_context(rest, done)
        )

    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    result = await score_placement(llm, done)
    await apply_placement(session, learner.id, result)
    context = {"result": result, **await _learn_context(session, learner.id)}
    return templates.TemplateResponse(request, "onboarding/result.html", context)
