from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerDep, LearnerIdDep
from soltura.learner.models import StudyStep
from soltura.llm.client import LLMClient, get_llm
from soltura.reading.topics import TOPICS
from soltura.reading.views import split_for_reading
from soltura.templating import templates
from soltura.use_cases.reading import prepare_text, save_tapped_word, tap_word
from soltura.use_cases.study import next_step_offer

router = APIRouter(prefix="/reading")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LLMDep = Annotated[LLMClient, Depends(get_llm)]


@router.get("", response_class=HTMLResponse)
async def reading_page(request: Request, topic: str = "") -> HTMLResponse:
    # A study session sends the learner here with the label of its topic, and the text
    # for it starts on its own.
    chosen = next((known for known in TOPICS if known.label == topic), None)
    return templates.TemplateResponse(
        request,
        "reading.html",
        {"topics": TOPICS, "auto_topic": chosen.prompt if chosen else None},
    )


@router.post("/text", response_class=HTMLResponse)
async def new_text(
    request: Request,
    session: SessionDep,
    learner: LearnerDep,
    learner_id: LearnerIdDep,
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
    now = datetime.now(UTC)
    prepared = await prepare_text(session, llm, learner, now, topic=topic, source_text=source)
    offer = await next_step_offer(session, learner_id, StudyStep.READING, now)
    return templates.TemplateResponse(
        request,
        "reading/text.html",
        {
            "prepared": prepared,
            "paragraphs": split_for_reading(prepared.text),
            "topic": topic or prepared.title,
            "study_step": offer,
        },
    )


@router.post("/tap", response_class=HTMLResponse)
async def tap(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    word: Annotated[str, Form()],
    sentence: Annotated[str, Form()],
    topic: Annotated[str, Form()] = "",
) -> HTMLResponse:
    result = await tap_word(session, llm, learner_id, word, sentence, datetime.now(UTC))
    return templates.TemplateResponse(
        request, "reading/gloss.html", {"result": result, "sentence": sentence, "topic": topic}
    )


@router.post("/save", response_class=HTMLResponse)
async def save(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    lemma: Annotated[str, Form()],
    sentence: Annotated[str, Form()],
    topic: Annotated[str, Form()] = "",
) -> HTMLResponse:
    await save_tapped_word(session, learner_id, lemma, sentence, datetime.now(UTC), topic or None)
    return templates.TemplateResponse(request, "reading/saved.html", {"lemma": lemma})
