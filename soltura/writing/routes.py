from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerIdDep
from soltura.llm.client import LLMClient, get_llm
from soltura.templating import templates
from soltura.use_cases.writing import journal_history, submit_entry
from soltura.writing.prompts import PROMPTS
from soltura.writing.service import InvalidText
from soltura.writing.views import PROBLEM_MESSAGE, entry_view

router = APIRouter(prefix="/journal")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]


@router.get("", response_class=HTMLResponse)
async def journal_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    history = await journal_history(session, learner_id)
    return templates.TemplateResponse(
        request,
        "journal.html",
        {"prompts": PROMPTS, "history": [entry_view(entry) for entry in history]},
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
        result = await submit_entry(session, llm, learner_id, prompt, text)
    except InvalidText as error:
        return templates.TemplateResponse(
            request,
            "reading/error.html",
            {"message": PROBLEM_MESSAGE[error.problem]},
            status_code=422,
        )
    return templates.TemplateResponse(request, "journal/result.html", {"entry": entry_view(result)})
