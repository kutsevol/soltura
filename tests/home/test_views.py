from soltura.home.service import HubSummary
from soltura.home.views import hub_view
from soltura.words.vocabulary import BandProgress, VocabularyMap


def test_the_hub_view_turns_the_vocabulary_into_the_known_summary() -> None:
    summary = HubSummary(
        due=2,
        learning=1,
        conjugation_due=3,
        placement_rank=250,
        vocabulary=VocabularyMap(bands=[BandProgress(1, 250, 10, 4, 1)]),
    )

    view = hub_view(summary)

    assert view.known_summary == "Знаю слів: 4 з 10"
    assert (view.due, view.learning, view.conjugation_due, view.placement_rank) == (2, 1, 3, 250)
