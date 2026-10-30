import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.config import settings
from soltura.db import get_engine, get_session
from soltura.templating import templates

logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    status: str = Field(description="Always 'ok' when the app and its database respond")


def configure_logging(level: str) -> None:
    # Uvicorn configures only its own loggers and leaves root without a handler,
    # so the app's records need a handler of their own to be visible at all.
    app_logger = logging.getLogger("soltura")
    app_logger.setLevel(level)
    if not app_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(levelname)s [%(name)s] %(message)s"))
        app_logger.addHandler(handler)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await get_engine().dispose()


def create_app() -> FastAPI:
    configure_logging(settings.logging.level)
    app = FastAPI(title="Soltura", lifespan=lifespan)

    @app.get("/health")
    async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> HealthResponse:
        await session.execute(text("SELECT 1"))
        return HealthResponse(status="ok")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "index.html")

    return app


app = create_app()
