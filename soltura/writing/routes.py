from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerIdDep
from soltura.learner.models import StudyStep
from soltura.llm.client import LLMClient, get_llm
from soltura.templating import templates
from soltura.use_cases.study import next_step_offer
from soltura.use_cases.writing import (
    error_summary,
    journal_history,
    session_prompt,
    submit_entry,
)
from soltura.writing.prompts import PROMPTS
from soltura.writing.service import InvalidText
from soltura.writing.views import PROBLEM_MESSAGE, category_view, entry_view

router = APIRouter(prefix="/journal")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]


@router.get("", response_class=HTMLResponse)
async def journal_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep, topic: str = ""
) -> HTMLResponse:
    history = await journal_history(session, learner_id)
    return templates.TemplateResponse(
        request,
        "journal.html",
        {
            "prompts": PROMPTS,
            "session_prompt": session_prompt(topic),
            "history": [entry_view(entry) for entry in history],
        },
    )


@router.get("/errors", response_class=HTMLResponse)
async def errors_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    summary = await error_summary(session, learner_id)
    return templates.TemplateResponse(
        request, "journal/errors.html", {"categories": [category_view(c) for c in summary]}
    )


@router.post("", response_class=HTMLResponse)
async def submit(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    text: Annotated[str, Form()],
    prompt: Annotated[str, Form()] = "",
) -> HTMLResponse:
    try:
        now = datetime.now(UTC)
        result = await submit_entry(session, llm, learner_id, prompt, text, now)
    except InvalidText as error:
        return templates.TemplateResponse(
            request,
            "reading/error.html",
            {"message": PROBLEM_MESSAGE[error.problem]},
            status_code=422,
        )
    offer = await next_step_offer(session, learner_id, StudyStep.WRITING, now)
    return templates.TemplateResponse(
        request, "journal/result.html", {"entry": entry_view(result), "study_step": offer}
    )
