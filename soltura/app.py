import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.config import settings
from soltura.db import get_engine, get_session
from soltura.home.routes import router as home_router
from soltura.llm.client import LLMNotConfiguredError, LLMUnavailableError
from soltura.onboarding.routes import router as onboarding_router
from soltura.reading.routes import router as reading_router
from soltura.templating import templates
from soltura.warmup.routes import router as warmup_router

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


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


async def llm_unavailable(request: Request, error: Exception) -> HTMLResponse:
    logger.warning(f"LLM unavailable: {error}")
    message = (
        "Модель не налаштована: додайте ANTHROPIC_API_KEY у .env і перезапустіть застосунок."
        if isinstance(error, LLMNotConfiguredError)
        else "Зараз не вдається отримати відповідь від моделі. Спробуйте ще раз."
    )
    return templates.TemplateResponse(
        request, "reading/error.html", {"message": message}, status_code=503
    )


def create_app() -> FastAPI:
    configure_logging(settings.logging.level)
    app = FastAPI(title="Soltura", lifespan=lifespan)
    app.add_exception_handler(LLMUnavailableError, llm_unavailable)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(home_router)
    app.include_router(reading_router)
    app.include_router(warmup_router)
    app.include_router(onboarding_router)

    @app.get("/health")
    async def health(session: Annotated[AsyncSession, Depends(get_session)]) -> HealthResponse:
        await session.execute(text("SELECT 1"))
        return HealthResponse(status="ok")

    return app


app = create_app()
