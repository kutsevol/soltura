from soltura.onboarding.service import (
    BANDS,
    PASS_SHARE,
    WEAK_BANDS_IN_A_ROW,
    WEAK_SHARE,
    PlacementResult,
)


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
