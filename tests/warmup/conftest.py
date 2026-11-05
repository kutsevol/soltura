from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.app import create_app
from soltura.config import settings
from soltura.db import get_session
from soltura.learner.models import Learner
from soltura.llm.client import get_llm
from tests.fakes import FakeLLM

SAVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


@pytest.fixture
async def warmup_client(
    session: AsyncSession, learner: Learner, llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", learner.telegram_user_id)
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_llm] = lambda: llm
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
