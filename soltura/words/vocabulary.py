from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.repository import get_vocabulary_bands
from soltura.onboarding.service import BANDS
from soltura.reading.service import UNRANKED

# The last band stops short of UNRANKED, where words the frequency seed never saw are saved.
OPEN_END = UNRANKED - 1
# The placement test's bands, then two for the vocabulary beyond them.
EDGES: tuple[tuple[int, int], ...] = (*BANDS, (6001, 8000), (8001, OPEN_END))


@dataclass(frozen=True)
class BandProgress:
    min_rank: int
    max_rank: int
    total: int
    known: int
    learning: int


@dataclass(frozen=True)
class VocabularyMap:
    bands: list[BandProgress]

    @property
    def total(self) -> int:
        return sum(band.total for band in self.bands)

    @property
    def known(self) -> int:
        return sum(band.known for band in self.bands)


async def build_vocabulary_map(session: AsyncSession, learner_id: int) -> VocabularyMap:
    counts = await get_vocabulary_bands(session, learner_id, EDGES)
    return VocabularyMap(
        bands=[
            BandProgress(low, high, band.total, band.known, band.learning)
            for (low, high), band in zip(EDGES, counts, strict=True)
        ]
    )
