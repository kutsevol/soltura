from soltura.home.views import hub_view
from soltura.use_cases.home import HubSummary
from soltura.words.vocabulary import BandProgress, VocabularyMap


def test_the_hub_view_turns_the_vocabulary_into_the_known_summary() -> None:
    summary = HubSummary(
        due=2,
        learning=1,
        conjugation_due=3,
        grammar_due=0,
        grammar_next=None,
        placement_rank=250,
        vocabulary=VocabularyMap(bands=[BandProgress(1, 250, 10, 4, 1)]),
    )

    view = hub_view(summary)

    assert view.known_summary == "Знаю слів: 4 з 10"
    assert (view.due, view.learning, view.conjugation_due, view.placement_rank) == (2, 1, 3, 250)


def _summary(grammar_due: int, grammar_next: str | None) -> HubSummary:
    return HubSummary(
        due=0,
        learning=0,
        conjugation_due=0,
        grammar_due=grammar_due,
        grammar_next=grammar_next,
        placement_rank=None,
        vocabulary=VocabularyMap(bands=[]),
    )


def test_the_grammar_tile_shows_the_exercises_due_before_the_next_lesson() -> None:
    assert hub_view(_summary(4, "ser чи estar")).grammar_status == "Вправ до повторення: 4"


def test_the_grammar_tile_names_the_next_lesson_when_nothing_is_due() -> None:
    assert hub_view(_summary(0, "ser чи estar")).grammar_status == "Наступне правило: ser чи estar"


def test_the_grammar_tile_says_so_when_every_unit_is_started() -> None:
    assert hub_view(_summary(0, None)).grammar_status == "Усі правила пройдено"
