from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.frequency import BANDS
from soltura.learner.repository import get_latest_placement_run

# Until onboarding measures the learner, the most frequent lemmas stand in for what a
# learner at A2 knows. wordfreq ranks web text, so everyday words like "cocina", "beber"
# or "cansado" sit between 1,500 and 3,000; at 1,500 live texts on family or sport
# came out at 83-88% and were stripped of exactly those words.
BASELINE_KNOWN_RANK = 3000
# A learner who passed no band of the placement test knows less than the first band.
FIRST_BAND_RANK = BANDS[0][1]


async def vocabulary_range(session: AsyncSession, learner_id: int) -> int:
    # The placement test is the only measure of the learner's vocabulary; without it the
    # baseline stands in. A run that passed no band still means "less than the baseline".
    run = await get_latest_placement_run(session, learner_id)
    if run is None:
        return BASELINE_KNOWN_RANK
    return max(run.known_rank, FIRST_BAND_RANK)


def knows_sentence(vocabulary: int) -> str:
    return f"The learner knows about the {vocabulary:,} most frequent Spanish words."
