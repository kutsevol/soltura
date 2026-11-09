from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import StudySession, StudyStep
from soltura.learner.repository import (
    count_activity,
    get_last_finished_study_session,
    get_open_study_session,
    set_study_step,
    start_study_session,
)
from soltura.reading.topics import TOPICS
from soltura.study.service import OPEN_FOR, next_step

TOPIC_LABELS = [topic.label for topic in TOPICS]


@dataclass(frozen=True)
class StudyProgress:
    topic: str
    step: StudyStep


@dataclass(frozen=True)
class StudySummary:
    topic: str
    reviews: int
    words_saved: int
    errors: int


def _progress(study: StudySession) -> StudyProgress:
    return StudyProgress(topic=study.topic, step=study.step)


async def start_session(
    session: AsyncSession, learner_id: int, topic: str, now: datetime
) -> StudyProgress:
    if topic not in TOPIC_LABELS:
        raise LookupError(f"No reading topic {topic}")
    study = await start_study_session(session, learner_id, topic, now)
    progress = _progress(study)
    await session.commit()
    return progress


async def open_session(
    session: AsyncSession, learner_id: int, now: datetime
) -> StudyProgress | None:
    study = await get_open_study_session(session, learner_id, now - OPEN_FOR)
    return _progress(study) if study else None


async def next_step_offer(
    session: AsyncSession, learner_id: int, module: StudyStep, now: datetime
) -> StudyStep | None:
    # A module offers "next" only while the session is on its own step, so opening
    # another screen on the side does not move the session.
    progress = await open_session(session, learner_id, now)
    return module if progress and progress.step == module else None


async def advance_session(
    session: AsyncSession, learner_id: int, expected: StudyStep, now: datetime
) -> StudyProgress:
    study = await get_open_study_session(session, learner_id, now - OPEN_FOR)
    if study is None:
        raise LookupError("The learner has no open study session")
    # The button carries the step the learner saw: a second tap, a retried request or an
    # old tab finds the session already moved on and must not skip another step.
    if study.step != expected:
        return _progress(study)
    await set_study_step(session, study, next_step(study.step), now)
    progress = _progress(study)
    await session.commit()
    return progress


async def session_summary(
    session: AsyncSession, learner_id: int, now: datetime
) -> StudySummary | None:
    study = await get_last_finished_study_session(session, learner_id, now - OPEN_FOR)
    if study is None or study.finished_at is None:
        return None
    activity = await count_activity(session, learner_id, study.started_at, study.finished_at)
    return StudySummary(
        topic=study.topic,
        reviews=activity.reviews,
        words_saved=activity.words_saved,
        errors=activity.errors,
    )
