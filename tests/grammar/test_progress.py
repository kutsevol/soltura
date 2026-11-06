from datetime import UTC, datetime, timedelta

from soltura.grammar.service import GrammarProgress, UnitProgress, build_progress
from soltura.grammar.units import all_units
from soltura.grammar.views import progress_view
from soltura.learner.repository import CardProgress

NOW = datetime(2026, 11, 5, 12, 0, tzinfo=UTC)
FIRST, SECOND = all_units()[:2]


def _card(
    key: str, stability: float | None, due: datetime, answers: int = 0, right: int = 0
) -> CardProgress:
    return CardProgress(key, stability, due, answers, right)


def test_progress_groups_the_cards_by_unit_and_counts_those_stable_for_a_week() -> None:
    soon, later = NOW + timedelta(hours=1), NOW + timedelta(days=3)
    cards = [
        _card(f"{SECOND.id}|e1", 20.0, later, answers=2, right=2),
        _card(f"{FIRST.id}|e1", 7.0, later, answers=3, right=1),
        _card(f"{FIRST.id}|e2", 3.2, soon, answers=1, right=0),
        _card(f"{FIRST.id}|e3", None, later),
    ]

    progress = build_progress(cards)

    assert [unit.unit.id for unit in progress.units] == [FIRST.id, SECOND.id]
    first = progress.units[0]
    assert (first.answers, first.right, first.solid, first.next_due) == (4, 1, 1, soon)
    assert progress.not_started == len(all_units()) - 2


def test_a_card_for_a_unit_that_no_longer_exists_is_ignored() -> None:
    progress = build_progress([_card("gone|e1", 30.0, NOW, answers=1, right=1)])

    assert progress == GrammarProgress(units=[], not_started=len(all_units()))


def _unit(answers: int, right: int, solid: int, next_due: datetime) -> UnitProgress:
    return UnitProgress(unit=FIRST, answers=answers, right=right, solid=solid, next_due=next_due)


def test_a_row_shows_the_share_right_the_solid_exercises_and_what_is_due() -> None:
    progress = GrammarProgress(units=[_unit(14, 11, 3, NOW - timedelta(hours=1))], not_started=2)

    view = progress_view(progress, NOW)

    [row] = view.rows
    assert row.title == FIRST.title
    assert row.answers_text == "Відповідей: 14, правильних: 79%"
    assert row.memory_text == f"У пам’яті: 3 з {len(FIRST.exercises)}"
    assert row.due_text == "Є що повторити"
    assert view.not_started == 2


def test_a_row_names_the_next_review_date_when_nothing_is_due_yet() -> None:
    progress = GrammarProgress(
        units=[_unit(0, 0, 0, datetime(2026, 11, 9, tzinfo=UTC))], not_started=0
    )

    [row] = progress_view(progress, NOW).rows

    assert row.answers_text == "Ще без відповідей"
    assert row.due_text == "Наступне повторення: 09.11"
