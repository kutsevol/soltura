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


def reading_score(texts: Sequence[ReadingText]) -> ReadingScore:
    # A text prepared below the coverage target was too hard for anyone at this vocabulary,
    # so a missed gist on it measures the text, not the learner.
    credits = [GIST_CREDIT[text.gist] for text in texts if text.gist and not text.below_target]
    if len(credits) < MIN_TEXTS:
        return ReadingScore(percent=None, counted=len(credits), needed=MIN_TEXTS)
    return ReadingScore(
        percent=round(100 * sum(credits) / len(credits)), counted=len(credits), needed=MIN_TEXTS
    )


@dataclass(frozen=True)
class ReadingProgress:
    score: ReadingScore
    texts: list[ReadingText]
