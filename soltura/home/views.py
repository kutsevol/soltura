from dataclasses import dataclass

from soltura.home.service import HubSummary
from soltura.words.views import known_summary


@dataclass(frozen=True)
class HubView:
    due: int
    learning: int
    known_summary: str
    conjugation_due: int
    placement_rank: int | None


def hub_view(summary: HubSummary) -> HubView:
    return HubView(
        due=summary.due,
        learning=summary.learning,
        known_summary=known_summary(summary.vocabulary),
        conjugation_due=summary.conjugation_due,
        placement_rank=summary.placement_rank,
    )
