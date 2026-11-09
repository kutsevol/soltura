from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import (
    ErrorKind,
    ErrorLog,
    Learner,
    Lexeme,
    Rating,
    ReviewSource,
    StudySession,
    StudyStep,
    WordContext,
)
from soltura.learner.repository import JournalError, save_journal_entry
from soltura.reading.topics import TOPICS
from soltura.srs.service import review, save_word
from soltura.use_cases.study import (
    advance_session,
    next_step_offer,
    open_session,
    session_summary,
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


# A sitting long before the tests run, so rows stamped by the database clock fall outside it.
STARTED = datetime(2020, 1, 1, 8, 0, tzinfo=UTC)
FINISHED = STARTED + timedelta(hours=1)


def _at(minutes: int) -> datetime:
    return STARTED + timedelta(minutes=minutes)


def _error(entry_id: int, learner_id: int, created_at: datetime) -> ErrorLog:
    return ErrorLog(
        entry_id=entry_id,
        learner_id=learner_id,
        kind=ErrorKind.OTHER,
        original="a",
        corrected="b",
        note="n",
        created_at=created_at,
    )


async def _finished_session(session: AsyncSession, learner: Learner) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, STARTED)
    for step in list(StudyStep)[:3]:
        await advance_session(session, learner.id, step, STARTED)
    await advance_session(session, learner.id, StudyStep.WRITING, FINISHED)


async def test_the_summary_counts_only_what_happened_during_the_session(
    session: AsyncSession, learner: Learner, other_learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None and other_learner.id is not None
    cards = await save_word(session, learner.id, lexemes[0].id or 0, "Una frase.", _at(-60))
    for minutes in (-30, 10, 20, 90):
        await review(session, cards[0], Rating.GOOD, ReviewSource.WARMUP, _at(minutes))
    for lexeme, minutes in ((lexemes[0], 10), (lexemes[0], 15), (lexemes[1], 20)):
        session.add(
            WordContext(
                learner_id=learner.id,
                lexeme_id=lexeme.id or 0,
                sentence="Una frase.",
                created_at=_at(minutes),
            )
        )
    # Rows the database or the application stamps with today's date fall outside a 2020 sitting.
    await save_word(session, learner.id, lexemes[2].id or 0, "Otra frase.", _at(30))
    real = JournalError(ErrorKind.OTHER, None, "x", "y", "n")
    entry = await save_journal_entry(session, learner.id, None, "b", "c", [real])
    for minutes in (-5, 30, 45, 70):
        session.add(_error(entry.id or 0, learner.id, _at(minutes)))
    # Everything the other learner did inside the same hour is theirs.
    theirs = await save_word(session, other_learner.id, lexemes[0].id or 0, "Una frase.", _at(0))
    await review(session, theirs[0], Rating.GOOD, ReviewSource.WARMUP, _at(30))
    session.add(
        WordContext(
            learner_id=other_learner.id,
            lexeme_id=lexemes[1].id or 0,
            sentence="Una frase.",
            created_at=_at(30),
        )
    )
    other_entry = await save_journal_entry(session, other_learner.id, None, "b", "c", [])
    session.add(_error(other_entry.id or 0, other_learner.id, _at(30)))
    await _finished_session(session, learner)

    summary = await session_summary(session, learner.id, FINISHED)

    assert summary is not None
    assert (summary.topic, summary.reviews, summary.words_saved, summary.errors) == (
        TOPIC,
        2,
        2,
        2,
    )


async def test_rows_exactly_at_the_start_and_the_finish_are_counted(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    cards = await save_word(session, learner.id, lexemes[0].id or 0, "Una frase.", _at(-60))
    entry = await save_journal_entry(session, learner.id, None, "b", "c", [])
    for minutes in (0, 60):
        await review(session, cards[0], Rating.GOOD, ReviewSource.WARMUP, _at(minutes))
        session.add(_error(entry.id or 0, learner.id, _at(minutes)))
    for lexeme, minutes in ((lexemes[0], 0), (lexemes[1], 60)):
        session.add(
            WordContext(
                learner_id=learner.id,
                lexeme_id=lexeme.id or 0,
                sentence="Una frase.",
                created_at=_at(minutes),
            )
        )
    await _finished_session(session, learner)

    summary = await session_summary(session, learner.id, FINISHED)

    assert summary is not None
    assert (summary.reviews, summary.words_saved, summary.errors) == (2, 2, 2)


async def test_an_open_or_replaced_session_has_no_summary(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    await start_session(session, learner.id, TOPIC, STARTED)
    assert await session_summary(session, learner.id, FINISHED) is None

    await start_session(session, learner.id, OTHER_TOPIC, FINISHED)

    assert await session_summary(session, learner.id, FINISHED) is None


async def test_the_summary_is_gone_after_twelve_hours_and_belongs_to_its_learner(
    session: AsyncSession, learner: Learner, other_learner: Learner
) -> None:
    assert learner.id is not None and other_learner.id is not None
    await _finished_session(session, learner)

    assert await session_summary(session, other_learner.id, FINISHED) is None
    assert await session_summary(session, learner.id, FINISHED + timedelta(hours=12)) is not None
    assert await session_summary(session, learner.id, FINISHED + timedelta(hours=13)) is None
