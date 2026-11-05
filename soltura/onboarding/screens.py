from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.onboarding.service import (
    MissedSummary,
    PlacementResult,
    get_latest_placement,
    missed_summary,
)
from soltura.reading.service import vocabulary_range
from soltura.words.vocabulary import VocabularyMap, build_vocabulary_map


@dataclass(frozen=True)
class ResultScreen:
    result: PlacementResult
    vocabulary: VocabularyMap
    reading_range: int
    missed: MissedSummary


async def result_screen(
    session: AsyncSession, learner_id: int, result: PlacementResult
) -> ResultScreen:
    return ResultScreen(
        result=result,
        vocabulary=await build_vocabulary_map(session, learner_id),
        reading_range=await vocabulary_range(session, learner_id),
        missed=await missed_summary(session, learner_id),
    )


async def latest_result_screen(session: AsyncSession, learner_id: int) -> ResultScreen | None:
    result = await get_latest_placement(session, learner_id)
    if result is None:
        return None
    return await result_screen(session, learner_id, result)
