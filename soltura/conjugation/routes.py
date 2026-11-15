from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.conjugation.forms import Person, Tense
from soltura.conjugation.service import ConjugationItem, PracticeItem
from soltura.conjugation.views import (
    ENDINGS_HEADER,
    card_view,
    endings_view,
    notes_view,
    practice_card_view,
    progress_view,
    result_view,
    tense_choices,
    verb_view,
)
from soltura.db import get_session
from soltura.learner.dependencies import LearnerIdDep
from soltura.templating import templates
from soltura.use_cases.conjugation import (
    InvalidPractice,
    PracticeProblem,
    answer_item,
    answer_notes,
    answer_practice,
    build_session,
    conjugation_progress,
    endings_table,
    new_sets_held_back,
    start_practice,
    verb_table,
)
from soltura.web import answer_duration_ms, now_ms, parse_state

router = APIRouter(prefix="/conjugation")

SessionDep = Annotated[AsyncSession, Depends(get_session)]

QUEUE = TypeAdapter(list[ConjugationItem])
STATE_ERROR = "Bad conjugation state"
PRACTICE_QUEUE = TypeAdapter(list[PracticeItem])
PRACTICE_ITEM = TypeAdapter(PracticeItem)
MAX_PRACTICE_QUEUE = len(Tense) * len(Person)
TENSE_VALUES = frozenset(tense.value for tense in Tense)
PRACTICE_MESSAGE = {
    PracticeProblem.UNKNOWN_VERB: "Не вдалося відмінювати це дієслово. Введіть інфінітив, напр. comer.",
    PracticeProblem.NO_TENSE: "Оберіть хоча б один час.",
}


def _card_context(item: ConjugationItem, queue: list[ConjugationItem]) -> dict[str, Any]:
    return {
        "card": card_view(item, len(queue)),
        "queue_json": QUEUE.dump_json(queue).decode(),
        "started_at": now_ms(),
    }


@router.get("", response_class=HTMLResponse)
async def conjugation_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    study = await build_session(session, learner_id, datetime.now(UTC))
    if not study.items:
        return templates.TemplateResponse(
            request, "conjugation.html", {"empty": True, "capped": study.capped}
        )
    first, *queue = study.items
    return templates.TemplateResponse(
        request, "conjugation.html", {"empty": False, **_card_context(first, queue)}
    )


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
        result = await answer_item(
            session, learner_id, card_id, answer, duration_ms, datetime.now(UTC)
        )
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN) from error
    return templates.TemplateResponse(
        request,
        "conjugation/result.html",
        {"result": result_view(result, answer, answer_notes(result)), "queue_json": queue},
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
        capped = await new_sets_held_back(session, learner_id, datetime.now(UTC))
        return templates.TemplateResponse(request, "conjugation/done.html", {"capped": capped})
    first, *rest = items
    return templates.TemplateResponse(request, "conjugation/card.html", _card_context(first, rest))


@router.get("/verbs/{verb}", response_class=HTMLResponse)
def verb_page(request: Request, learner_id: LearnerIdDep, verb: str) -> HTMLResponse:
    # Plain `def` routes run in the thread pool: the library's first load takes seconds.
    table = verb_table(verb)
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return templates.TemplateResponse(
        request,
        "conjugation/verb.html",
        {
            "verb": table.verb,
            "tenses": verb_view(table.forms),
            "notes": notes_view(table.notes),
        },
    )


@router.get("/endings", response_class=HTMLResponse)
def endings_page(request: Request, learner_id: LearnerIdDep) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "conjugation/endings.html",
        {"header": ENDINGS_HEADER, "tenses": endings_view(endings_table())},
    )


@router.get("/progress", response_class=HTMLResponse)
async def progress_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    accuracy = await conjugation_progress(session, learner_id)
    return templates.TemplateResponse(
        request, "conjugation/progress.html", {"rows": progress_view(accuracy)}
    )


def _practice_context(item: PracticeItem, queue: list[PracticeItem]) -> dict[str, Any]:
    return {
        "card": practice_card_view(item, len(queue)),
        "item": item,
        "queue_json": PRACTICE_QUEUE.dump_json(queue).decode(),
    }


@router.get("/practice", response_class=HTMLResponse)
def practice_page(request: Request, learner_id: LearnerIdDep, verb: str = "") -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "conjugation/practice.html",
        {"verb": verb.strip()[:30], "tenses": tense_choices()},
    )


@router.post("/practice/start", response_class=HTMLResponse)
def practice_start(
    request: Request,
    learner_id: LearnerIdDep,
    verb: Annotated[str, Form()] = "",
    tense: Annotated[list[str] | None, Form()] = None,
) -> HTMLResponse:
    chosen = [Tense(value) for value in tense or [] if value in TENSE_VALUES]
    try:
        queue = start_practice(verb, chosen)
    except InvalidPractice as error:
        return templates.TemplateResponse(
            request,
            "conjugation/message.html",
            {"message": PRACTICE_MESSAGE[error.problem]},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    first, *rest = queue
    return templates.TemplateResponse(
        request, "conjugation/practice_card.html", _practice_context(first, rest)
    )


@router.post("/practice/answer", response_class=HTMLResponse)
def practice_answer(
    request: Request,
    learner_id: LearnerIdDep,
    verb: Annotated[str, Form()],
    tense: Annotated[str, Form()],
    person: Annotated[str, Form()],
    queue: Annotated[str, Form()],
    answer: Annotated[str, Form()] = "",
    give_up: Annotated[bool, Form()] = False,
) -> HTMLResponse:
    if give_up:
        answer = ""
    rest = parse_state(PRACTICE_QUEUE, queue, STATE_ERROR)
    if len(rest) >= MAX_PRACTICE_QUEUE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=STATE_ERROR)
    try:
        item = PRACTICE_ITEM.validate_python({"verb": verb, "tense": tense, "person": person})
        result = answer_practice(item, answer)
    except (ValidationError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=STATE_ERROR) from error
    return templates.TemplateResponse(
        request,
        "conjugation/result.html",
        {
            "result": result_view(result, answer, answer_notes(result)),
            "queue_json": queue,
            "next_url": "/conjugation/practice/next",
            "next_target": "#practice",
        },
    )


@router.post("/practice/next", response_class=HTMLResponse)
def practice_next(
    request: Request, learner_id: LearnerIdDep, queue: Annotated[str, Form()]
) -> HTMLResponse:
    items = parse_state(PRACTICE_QUEUE, queue, STATE_ERROR)
    if len(items) >= MAX_PRACTICE_QUEUE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=STATE_ERROR)
    if not items:
        return templates.TemplateResponse(request, "conjugation/practice_done.html", {})
    first, *rest = items
    return templates.TemplateResponse(
        request, "conjugation/practice_card.html", _practice_context(first, rest)
    )
