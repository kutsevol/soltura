from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import current_learner
from soltura.learner.models import Learner, LexemeStatus
from soltura.learner.repository import get_saved_words
from soltura.templating import templates

router = APIRouter(prefix="/words")

SessionDep = Annotated[AsyncSession, Depends(get_session)]
LearnerDep = Annotated[Learner, Depends(current_learner)]

STATUS_LABEL = {LexemeStatus.LEARNING: "Вивчаю", LexemeStatus.KNOWN: "Знаю"}


def due_label(due: datetime, now: datetime) -> str:
    return "зараз" if due <= now else due.astimezone(UTC).strftime("%d.%m.%Y")


async def _words_context(session: AsyncSession, learner: Learner, search: str) -> dict[str, object]:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    now = datetime.now(UTC)
    return {
        "words": await get_saved_words(session, learner.id, search.strip()),
        "search": search.strip(),
        "now": now,
        "due_label": due_label,
        "status_label": STATUS_LABEL,
    }


@router.get("", response_class=HTMLResponse)
async def words_page(
    request: Request, session: SessionDep, learner: LearnerDep, q: str = ""
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "words.html", await _words_context(session, learner, q)
    )


@router.get("/search", response_class=HTMLResponse)
async def search_words(
    request: Request, session: SessionDep, learner: LearnerDep, q: str = ""
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "words/list.html", await _words_context(session, learner, q)
    )
