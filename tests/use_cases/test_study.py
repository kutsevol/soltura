from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner, StudySession, StudyStep
from soltura.reading.topics import TOPICS
from soltura.use_cases.study import (
    advance_session,
    next_step_offer,
    open_session,
    start_session,
)

NOW = datetime(2026, 11, 9, 8, 0, tzinfo=UTC)
TOPIC = TOPICS[0].label
OTHER_TOPIC = TOPICS[1].label


async def test_a_started_session_is_open_on_the_warm_up(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    started = await start_session(session, learner.id, TOPIC, NOW)

    assert (started.topic, started.step) == (TOPIC, StudyStep.WARMUP)
    assert await open_session(session, learner.id, NOW) == started


async def test_a_topic_that_is_not_offered_starts_nothing(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    with pytest.raises(LookupError):
        await start_session(session, learner.id, "forged topic", NOW)

    assert await open_session(session, learner.id, NOW) is None


async def test_starting_a_session_closes_the_one_that_was_open(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    await start_session(session, learner.id, OTHER_TOPIC, NOW + timedelta(hours=1))

    opened = await open_session(session, learner.id, NOW + timedelta(hours=1))
    assert opened is not None and opened.topic == OTHER_TOPIC
    sessions = (await session.execute(select(StudySession))).scalars().all()
    assert sorted(study.finished_at is None for study in sessions) == [False, True]


async def test_advancing_walks_the_steps_and_ends_at_done(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    steps = [StudyStep.WARMUP]
    for _ in range(4):
        steps.append((await advance_session(session, learner.id, steps[-1], NOW)).step)

    assert steps == [
        StudyStep.WARMUP,
        StudyStep.READING,
        StudyStep.GRAMMAR,
        StudyStep.WRITING,
        StudyStep.DONE,
    ]
    assert await open_session(session, learner.id, NOW) is None
    with pytest.raises(LookupError):
        await advance_session(session, learner.id, StudyStep.DONE, NOW)


async def test_a_second_tap_on_the_same_step_does_not_skip_a_step(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    first = await advance_session(session, learner.id, StudyStep.WARMUP, NOW)
    second = await advance_session(session, learner.id, StudyStep.WARMUP, NOW)

    assert (first.step, second.step) == (StudyStep.READING, StudyStep.READING)


async def test_two_open_sessions_of_one_learner_cannot_exist(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    with pytest.raises(IntegrityError):
        async with session.begin_nested():
            session.add(StudySession(learner_id=learner.id, topic=OTHER_TOPIC))


@pytest.mark.parametrize(
    ("age", "is_open"),
    [
        (timedelta(hours=11, minutes=59), True),
        (timedelta(hours=12), True),
        (timedelta(hours=12, minutes=1), False),
    ],
)
async def test_a_session_older_than_twelve_hours_counts_as_closed(
    session: AsyncSession, learner: Learner, age: timedelta, is_open: bool
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    opened = await open_session(session, learner.id, NOW + age)

    assert (opened is not None) == is_open


async def test_a_stale_session_cannot_be_advanced(session: AsyncSession, learner: Learner) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    with pytest.raises(LookupError):
        await advance_session(session, learner.id, StudyStep.WARMUP, NOW + timedelta(days=1))


async def test_a_session_belongs_to_its_learner(
    session: AsyncSession, learner: Learner, other_learner: Learner
) -> None:
    assert learner.id is not None and other_learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    assert await open_session(session, other_learner.id, NOW) is None
    with pytest.raises(LookupError):
        await advance_session(session, other_learner.id, StudyStep.WARMUP, NOW)


async def test_starting_and_advancing_are_committed(
    session: AsyncSession, learner: Learner, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert learner.id is not None
    commits: list[int] = []
    commit = session.commit

    async def counting_commit() -> None:
        commits.append(1)
        await commit()

    monkeypatch.setattr(session, "commit", counting_commit)

    await start_session(session, learner.id, TOPIC, NOW)
    await advance_session(session, learner.id, StudyStep.WARMUP, NOW)

    assert commits == [1, 1]


@pytest.mark.parametrize("on", list(StudyStep)[:4])
@pytest.mark.parametrize("module", list(StudyStep)[:4])
async def test_a_module_is_offered_the_next_step_only_while_the_session_is_on_it(
    session: AsyncSession, learner: Learner, on: StudyStep, module: StudyStep
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)
    for step in list(StudyStep)[: list(StudyStep).index(on)]:
        await advance_session(session, learner.id, step, NOW)

    offer = await next_step_offer(session, learner.id, module, NOW)

    assert offer == (module if module == on else None)


async def test_no_module_is_offered_the_next_step_without_an_open_session(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, NOW)

    later = NOW + timedelta(hours=13)

    assert await next_step_offer(session, learner.id, StudyStep.WARMUP, later) is None
