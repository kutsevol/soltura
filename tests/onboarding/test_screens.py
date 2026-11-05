from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner
from soltura.onboarding.screens import latest_result_screen, result_screen
from soltura.onboarding.service import BandScore, PlacementResult, apply_placement


async def test_a_learner_without_a_run_has_no_result_screen(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    assert await latest_result_screen(session, learner.id) is None


async def test_the_result_screen_carries_the_reading_range_of_the_saved_run(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    result = PlacementResult(known_rank=1000, bands=[BandScore(0, 250, 8, 8)])
    await apply_placement(session, learner.id, result)

    screen = await result_screen(session, learner.id, result)

    assert screen.result == result
    assert screen.reading_range == 1000
    assert screen.missed.total == 0


async def test_a_run_that_passed_no_band_still_reads_at_the_first_band(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    result = PlacementResult(known_rank=0, bands=[BandScore(0, 250, 2, 8)])
    await apply_placement(session, learner.id, result)

    screen = await latest_result_screen(session, learner.id)

    assert screen is not None
    assert screen.reading_range == 250
