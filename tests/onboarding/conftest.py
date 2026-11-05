from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.app import create_app
from soltura.config import settings
from soltura.db import get_session
from soltura.learner.models import Learner
from soltura.llm.client import get_llm
from tests.conftest import JudgeByAnswer


@pytest.fixture
async def onboarding_client(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", learner.telegram_user_id)
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_llm] = lambda: judge
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
