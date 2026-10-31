from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.config import settings
from soltura.db import get_session
from soltura.learner.models import Learner
from soltura.learner.repository import get_or_create_learner


async def current_learner(session: Annotated[AsyncSession, Depends(get_session)]) -> Learner:
    telegram_user_id = settings.auth.dev_telegram_user_id
    if telegram_user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    return await get_or_create_learner(session, telegram_user_id)
