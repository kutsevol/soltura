from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import StudySession, StudyStep
from soltura.learner.repository import (
    get_open_study_session,
    set_study_step,
    start_study_session,
)
from soltura.reading.topics import TOPICS
from soltura.study.service import OPEN_FOR, next_step


@dataclass(frozen=True)
class StudyProgress:
    topic: str
    step: StudyStep


def _progress(study: StudySession) -> StudyProgress:
    return StudyProgress(topic=study.topic, step=study.step)


async def start_session(
    session: AsyncSession, learner_id: int, topic: str, now: datetime
) -> StudyProgress:
    if topic not in {known.label for known in TOPICS}:
        raise LookupError(f"No reading topic {topic}")
    study = await start_study_session(session, learner_id, topic, now)
    await session.commit()
    return _progress(study)


async def open_session(
    session: AsyncSession, learner_id: int, now: datetime
) -> StudyProgress | None:
    study = await get_open_study_session(session, learner_id, now - OPEN_FOR)
    return _progress(study) if study else None


async def advance_session(session: AsyncSession, learner_id: int, now: datetime) -> StudyProgress:
    study = await get_open_study_session(session, learner_id, now - OPEN_FOR)
    if study is None:
        raise LookupError("The learner has no open study session")
    await set_study_step(session, study, next_step(study.step), now)
    await session.commit()
    return _progress(study)
