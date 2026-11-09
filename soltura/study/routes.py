from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.learner.dependencies import LearnerIdDep
from soltura.learner.models import StudyStep
from soltura.study.views import SESSION_HREF, landing_href, study_view
from soltura.templating import templates
from soltura.use_cases.study import TOPIC_LABELS, advance_session, open_session, start_session

router = APIRouter(prefix="/study")

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _redirect(href: str) -> RedirectResponse:
    return RedirectResponse(href, status_code=status.HTTP_303_SEE_OTHER)


@router.get("", response_class=HTMLResponse)
async def study_page(
    request: Request, session: SessionDep, learner_id: LearnerIdDep
) -> HTMLResponse:
    progress = await open_session(session, learner_id, datetime.now(UTC))
    view = study_view(progress.topic, progress.step) if progress else None
    return templates.TemplateResponse(request, "study.html", {"topics": TOPIC_LABELS, "view": view})


@router.post("/start")
async def start(
    session: SessionDep, learner_id: LearnerIdDep, topic: Annotated[str, Form()]
) -> RedirectResponse:
    try:
        progress = await start_session(session, learner_id, topic, datetime.now(UTC))
    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown topic"
        ) from error
    return _redirect(landing_href(progress.step))


@router.post("/next")
async def next_step(
    session: SessionDep, learner_id: LearnerIdDep, step: Annotated[StudyStep, Form()]
) -> RedirectResponse:
    try:
        progress = await advance_session(session, learner_id, step, datetime.now(UTC))
    except LookupError:
        return _redirect(SESSION_HREF)
    return _redirect(landing_href(progress.step))
