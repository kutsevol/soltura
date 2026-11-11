import math
from collections.abc import Sequence
from dataclasses import dataclass

from soltura.learner.models import GistResult, ReadingText

RECENT_TEXTS = 10
MIN_TEXTS = 3

# A partly understood text is half a text followed.
GIST_CREDIT = {GistResult.UNDERSTOOD: 1.0, GistResult.PARTLY: 0.5, GistResult.MISSED: 0.0}


@dataclass(frozen=True)
class ReadingScore:
    percent: int | None
    counted: int
    needed: int


def reading_score(counted: Sequence[ReadingText]) -> ReadingScore:
    credits = [GIST_CREDIT[text.gist] for text in counted if text.gist]
    if len(credits) < MIN_TEXTS:
        return ReadingScore(percent=None, counted=len(credits), needed=MIN_TEXTS)
    # Rounded half up: round() would give 12 for 12.5 and 38 for 37.5.
    percent = math.floor(100 * sum(credits) / len(credits) + 0.5)
    return ReadingScore(percent=percent, counted=len(credits), needed=MIN_TEXTS)


@dataclass(frozen=True)
class ReadingProgress:
    score: ReadingScore
    texts: list[ReadingText]
