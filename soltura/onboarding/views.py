from dataclasses import dataclass

from soltura.onboarding.service import (
    BANDS,
    PASS_SHARE,
    WEAK_BANDS_IN_A_ROW,
    WEAK_SHARE,
    LearnOutcome,
    PlacementItem,
    PlacementResult,
)
from soltura.practice.text import split_around
from soltura.use_cases.onboarding import ResultScreen
from soltura.words.views import known_summary


def _percent(share: float) -> str:
    return f"{round(share * 100)}%"


def explanation(result: PlacementResult) -> list[str]:
    asked = sum(band.total for band in result.bands)
    right = sum(band.correct for band in result.bands)
    lines = [
        f"Питань: {asked}, правильних відповідей: {right}.",
        f"Група слів пройдена, якщо правильних щонайменше {_percent(PASS_SHARE)}. "
        "Знайомими стають усі слова до першої групи, яку не пройдено.",
    ]
    failed = next((band for band in result.bands if band.correct / band.total < PASS_SHARE), None)
    if failed is None:
        lines.append("Усі групи, про які питали, пройдені.")
    else:
        lines.append(
            f"Серія пройдених груп обірвалась на групі до {failed.max_rank}: "
            f"{failed.correct} з {failed.total}."
        )
    above = sum(
        1
        for word in result.words
        if word.verdict == "correct" and BANDS[word.band][1] > result.known_rank
    )
    if above:
        lines.append(
            f"Окремо знайомими позначено слова, на які ви відповіли правильно в рідших групах: {above}."
        )
    if len(result.bands) < len(BANDS):
        lines.append(
            f"Тест зупинився після групи до {result.bands[-1].max_rank}: "
            f"{WEAK_BANDS_IN_A_ROW} групи поспіль мали не більше {_percent(WEAK_SHARE)} правильних, "
            "а слова далі лише рідші."
        )
    return lines


@dataclass(frozen=True)
class CardView:
    before: str
    target: str
    after: str
    position: int
    total: int
    checking: bool


def card_view(queue: list[PlacementItem], answered: list[PlacementItem]) -> CardView:
    current = queue[0]
    before, target, after = split_around(current.sentence, current.target_form) or (
        current.sentence,
        "",
        "",
    )
    return CardView(
        before=before,
        target=target,
        after=after,
        position=len(answered) + 1,
        total=len(answered) + len(queue),
        # The last word of a band is followed by a wait while its answers are judged.
        checking=len(queue) == 1 or queue[1].band != current.band,
    )


@dataclass(frozen=True)
class ResultView:
    result: PlacementResult
    explanation: list[str]
    reading_range: int
    known_summary: str
    missed_total: int
    missed_batch: int


def result_view(screen: ResultScreen) -> ResultView:
    return ResultView(
        result=screen.result,
        explanation=explanation(screen.result),
        reading_range=screen.reading_range,
        known_summary=known_summary(screen.vocabulary),
        missed_total=screen.missed.total,
        missed_batch=screen.missed.batch,
    )


@dataclass(frozen=True)
class LearnView:
    added: int
    missed_total: int
    missed_batch: int


def learn_view(outcome: LearnOutcome) -> LearnView:
    return LearnView(
        added=outcome.added,
        missed_total=outcome.missed.total,
        missed_batch=outcome.missed.batch,
    )
