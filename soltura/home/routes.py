from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.db import get_session
from soltura.home.views import hub_view
from soltura.learner.dependencies import LearnerIdDep
from soltura.templating import templates
from soltura.use_cases.home import hub_summary

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home_page(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    learner_id: LearnerIdDep,
) -> HTMLResponse:
    summary = await hub_summary(session, learner_id, datetime.now(UTC))
    return templates.TemplateResponse(request, "home.html", vars(hub_view(summary)))
