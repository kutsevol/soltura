from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerDep, LearnerIdDep
from soltura.learner.models import StudyStep
from soltura.llm.client import LLMClient, get_llm
from soltura.reading.service import (
    MAX_FACT_ANSWER,
    MAX_GIST_ANSWER,
    MAX_GIST_TEXT,
    MAX_QUESTION,
    MAX_QUESTIONS,
)
from soltura.reading.topics import TOPICS
from soltura.reading.views import FACT_LABEL, GIST_LABEL, progress_view, split_for_reading
from soltura.templating import templates
from soltura.use_cases.reading import (
    check_answers,
    check_gist,
    make_questions,
    prepare_text,
    reading_progress,
    save_tapped_word,
    tap_word,
    translations_in_text,
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
    translations = await translations_in_text(session, learner_id, prepared.text)
    return templates.TemplateResponse(
        request,
        "reading/text.html",
        {
            "prepared": prepared,
            "paragraphs": split_for_reading(prepared.text, translations),
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
    translation: Annotated[str, Form()] = "",
) -> HTMLResponse:
    await save_tapped_word(
        session, learner_id, lemma, sentence, datetime.now(UTC), topic or None, translation
    )
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


def _refused(request: Request, message: str) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "reading/error.html", {"message": message}, status_code=422
    )


@router.post("/questions", response_class=HTMLResponse)
async def fact_questions(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    text_id: Annotated[int, Form()],
    text: Annotated[str, Form()],
) -> HTMLResponse:
    if not text.strip() or len(text) > MAX_GIST_TEXT:
        return _refused(request, "Текст порожній або задовгий.")
    try:
        asked = await make_questions(session, llm, learner_id, text_id, text)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from error
    return templates.TemplateResponse(
        request,
        "reading/questions.html",
        {"questions": asked, "text_id": text_id, "text": text, "max_answer": MAX_FACT_ANSWER},
    )


@router.post("/answers", response_class=HTMLResponse)
async def fact_answers(
    request: Request,
    session: SessionDep,
    learner_id: LearnerIdDep,
    llm: LLMDep,
    text_id: Annotated[int, Form()],
    text: Annotated[str, Form()],
    questions: Annotated[list[str] | None, Form()] = None,
    answers: Annotated[list[str] | None, Form()] = None,
) -> HTMLResponse:
    asked = [question.strip() for question in questions or []]
    # A browser sends a newline as two characters, which the limit must not count twice.
    given = [answer.replace("\r\n", "\n").strip() for answer in answers or []]
    if not asked or len(asked) > MAX_QUESTIONS or len(asked) != len(given):
        return _refused(request, "Запитання не збігаються з відповідями.")
    if not text.strip() or not all(asked) or not all(given):
        return _refused(request, "Напишіть відповідь на кожне запитання.")
    if (
        len(text) > MAX_GIST_TEXT
        or any(len(question) > MAX_QUESTION for question in asked)
        or any(len(answer) > MAX_FACT_ANSWER for answer in given)
    ):
        return _refused(request, "Відповідь, запитання або текст задовгі.")
    try:
        verdicts = await check_answers(session, llm, learner_id, text_id, text, asked, given)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from error
    rows = [
        {
            "question": question,
            "answer": answer,
            "label": FACT_LABEL[verdict.verdict],
            "reason": verdict.reason,
        }
        for question, answer, verdict in zip(asked, given, verdicts, strict=True)
    ]
    return templates.TemplateResponse(request, "reading/answers.html", {"rows": rows})


@router.get("/progress", response_class=HTMLResponse)
async def progress_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    progress = await reading_progress(session, learner_id)
    return templates.TemplateResponse(
        request, "reading/progress.html", {"progress": progress_view(progress)}
    )
