from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import current_learner
from soltura.learner.models import Learner
from soltura.llm.client import LLMClient, get_llm
from soltura.reading.service import prepare_text, save_tapped_word, split_for_reading, tap_word
from soltura.reading.topics import TOPICS
from soltura.templating import templates

router = APIRouter(prefix="/reading")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LearnerDep = Annotated[Learner, Depends(current_learner)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]


def _learner_id(learner: Learner) -> int:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    return learner.id


@router.get("", response_class=HTMLResponse)
async def reading_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "reading.html", {"topics": TOPICS})


@router.post("/text", response_class=HTMLResponse)
async def new_text(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    llm: LLMDep,
    topic: Annotated[str, Form()] = "",
    source_text: Annotated[str, Form()] = "",
) -> HTMLResponse:
    topic, source = topic.strip(), source_text.strip() or None
    if not topic and source is None:
        return templates.TemplateResponse(
            request,
            "reading/error.html",
            {"message": "Вкажіть тему або вставте текст."},
            status_code=422,
        )
    prepared = await prepare_text(
        session, llm, learner, datetime.now(UTC), topic=topic, source_text=source
    )
    return templates.TemplateResponse(
        request,
        "reading/text.html",
        {
            "prepared": prepared,
            "paragraphs": split_for_reading(prepared.text),
            "topic": topic or prepared.title,
        },
    )


@router.post("/tap", response_class=HTMLResponse)
async def tap(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    llm: LLMDep,
    word: Annotated[str, Form()],
    sentence: Annotated[str, Form()],
    topic: Annotated[str, Form()] = "",
) -> HTMLResponse:
    result = await tap_word(session, llm, _learner_id(learner), word, sentence, datetime.now(UTC))
    return templates.TemplateResponse(
        request, "reading/gloss.html", {"result": result, "sentence": sentence, "topic": topic}
    )


@router.post("/save", response_class=HTMLResponse)
async def save(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    lemma: Annotated[str, Form()],
    sentence: Annotated[str, Form()],
    topic: Annotated[str, Form()] = "",
) -> HTMLResponse:
    await save_tapped_word(
        session, _learner_id(learner), lemma, sentence, datetime.now(UTC), topic or None
    )
    return templates.TemplateResponse(request, "reading/saved.html", {"lemma": lemma})
