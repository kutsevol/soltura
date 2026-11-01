from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import current_learner
from soltura.learner.models import Learner
from soltura.learner.repository import count_due_cards, count_learning_words
from soltura.templating import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    learner: Annotated[Learner, Depends(current_learner)],
) -> HTMLResponse:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    due = await count_due_cards(session, learner.id, datetime.now(UTC))
    learning = await count_learning_words(session, learner.id)
    return templates.TemplateResponse(request, "home.html", {"due": due, "learning": learning})
