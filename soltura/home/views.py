from dataclasses import dataclass

from soltura.use_cases.home import HubSummary
from soltura.words.views import known_summary


@dataclass(frozen=True)
class HubView:
    due: int
    learning: int
    known_summary: str
    conjugation_due: int
    grammar_status: str
    placement_rank: int | None


def _grammar_status(summary: HubSummary) -> str:
    if summary.grammar_due:
        return f"Вправ до повторення: {summary.grammar_due}"
    if summary.grammar_next:
        return f"Наступне правило: {summary.grammar_next}"
    return "Усі правила пройдено"


def hub_view(summary: HubSummary) -> HubView:
    return HubView(
        due=summary.due,
        learning=summary.learning,
        known_summary=known_summary(summary.vocabulary),
        conjugation_due=summary.conjugation_due,
        grammar_status=_grammar_status(summary),
        placement_rank=summary.placement_rank,
    )
