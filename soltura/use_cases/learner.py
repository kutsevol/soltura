from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner
from soltura.learner.repository import get_or_create_learner


async def identify_learner(session: AsyncSession, telegram_user_id: int) -> Learner:
    # The one place a request becomes a learner: a Telegram login will check its signed
    # data before this call, and nothing else needs to change.
    return await get_or_create_learner(session, telegram_user_id)
