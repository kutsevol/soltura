import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.config import settings
from soltura.learner.dependencies import current_learner


async def test_current_learner_rejects_requests_without_dev_login(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", None)

    with pytest.raises(HTTPException) as error:
        await current_learner(session)

    assert error.value.status_code == 401


async def test_current_learner_uses_the_dev_telegram_user(
    session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", 777)

    learner = await current_learner(session)

    assert learner.telegram_user_id == 777
