from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.grammar.units import all_units
from soltura.learner.models import Learner, MemoryCard, PlacementRun
from soltura.use_cases.grammar import start_unit
from soltura.use_cases.home import hub_summary

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


async def test_a_new_learner_has_nothing_due_and_no_placement(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    summary = await hub_summary(session, learner.id, NOW)

    assert (summary.due, summary.learning, summary.conjugation_due) == (0, 0, 0)
    assert summary.placement_rank is None
    assert summary.vocabulary.known == 0


async def test_the_counts_are_the_learners_words_forms_and_placement(
    session: AsyncSession,
    learner: Learner,
    saved_word: None,
    due_conjugation_card: MemoryCard,
    placement_run: PlacementRun,
) -> None:
    assert learner.id is not None

    summary = await hub_summary(session, learner.id, NOW)

    assert (summary.due, summary.learning, summary.conjugation_due) == (2, 1, 1)
    assert summary.placement_rank == 500


async def test_a_placement_that_passed_no_band_is_a_rank_of_zero_not_no_placement(
    session: AsyncSession, learner: Learner, failed_placement_run: PlacementRun
) -> None:
    assert learner.id is not None

    summary = await hub_summary(session, learner.id, NOW)

    assert summary.placement_rank == 0


async def test_the_hub_counts_grammar_exercises_and_names_the_next_lesson(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    first, second = all_units()[:2]
    await start_unit(session, learner.id, first.id, NOW)

    summary = await hub_summary(session, learner.id, NOW)

    assert summary.grammar_due == len(first.exercises)
    assert summary.grammar_next == second.title


async def test_a_new_learner_is_next_in_line_for_the_first_lesson(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    summary = await hub_summary(session, learner.id, NOW)

    assert (summary.grammar_due, summary.grammar_next) == (0, all_units()[0].title)
