from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import current_learner
from soltura.learner.models import Learner, UnitKind
from soltura.learner.repository import (
    count_due_cards,
    count_learning_words,
    get_latest_placement_run,
)
from soltura.templating import templates
from soltura.words.views import known_summary
from soltura.words.vocabulary import build_vocabulary_map

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    learner: Annotated[Learner, Depends(current_learner)],
) -> HTMLResponse:
    if learner.id is None:
        raise ValueError("current_learner returned an unsaved learner")
    due = await count_due_cards(session, learner.id, datetime.now(UTC), UnitKind.WORD)
    learning = await count_learning_words(session, learner.id)
    conjugation_due = await count_due_cards(
        session, learner.id, datetime.now(UTC), UnitKind.CONJUGATION
    )
    placement = await get_latest_placement_run(session, learner.id)
    vocabulary = await build_vocabulary_map(session, learner.id)
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "due": due,
            "learning": learning,
            "known_summary": known_summary(vocabulary),
            "conjugation_due": conjugation_due,
            "placement_rank": placement.known_rank if placement else None,
        },
    )
