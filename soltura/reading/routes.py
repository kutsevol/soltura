from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerDep, LearnerIdDep
from soltura.learner.models import StudyStep
from soltura.llm.client import LLMClient, get_llm
from soltura.reading.service import MAX_GIST_ANSWER, MAX_GIST_TEXT
from soltura.reading.topics import TOPICS
from soltura.reading.views import GIST_LABEL, progress_view, split_for_reading
from soltura.templating import templates
from soltura.use_cases.reading import (
    check_gist,
    prepare_text,
    reading_progress,
    save_tapped_word,
    tap_word,
)
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
            "text_id": prepared.text_id,
            "study_step": offer,
            "max_gist_answer": MAX_GIST_ANSWER,
        },
    )


@router.post("/tap", response_class=HTMLResponse)
async def tap(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    text_id: Annotated[int, Form()],
    word: Annotated[str, Form()],
    sentence: Annotated[str, Form()],
    topic: Annotated[str, Form()] = "",
) -> HTMLResponse:
    try:
        result = await tap_word(
            session, llm, learner_id, text_id, word, sentence, datetime.now(UTC)
        )
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from error
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


@router.post("/gist", response_class=HTMLResponse)
async def gist(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    text_id: Annotated[int, Form()],
    text: Annotated[str, Form()],
    answer: Annotated[str, Form()] = "",
) -> HTMLResponse:
    # A browser sends a newline as two characters, which the limit must not count twice.
    answer = answer.replace("\r\n", "\n").strip()
    message = None
    if not answer:
        message = "Напишіть хоча б кілька слів."
    elif len(answer) > MAX_GIST_ANSWER or len(text) > MAX_GIST_TEXT:
        message = "Відповідь або текст задовгі."
    if message:
        return templates.TemplateResponse(
            request, "reading/error.html", {"message": message}, status_code=422
        )
    try:
        verdict = await check_gist(session, llm, learner_id, text_id, text, answer)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from error
    return templates.TemplateResponse(
        request,
        "reading/gist.html",
        {"verdict": verdict, "label": GIST_LABEL[verdict.verdict]},
    )


@router.get("/progress", response_class=HTMLResponse)
async def progress_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    progress = await reading_progress(session, learner_id)
    return templates.TemplateResponse(
        request, "reading/progress.html", {"progress": progress_view(progress)}
    )
