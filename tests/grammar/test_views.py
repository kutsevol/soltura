from soltura.grammar.service import ExerciseResult, GrammarItem
from soltura.grammar.units import get_unit
from soltura.grammar.views import card_view, result_view
from soltura.learner.models import Rating
from soltura.practice.checking import SpanishCheck


def test_the_card_splits_the_sentence_at_the_gap_and_keeps_every_option() -> None:
    unit = get_unit("ser_estar")
    assert unit is not None
    exercise = unit.exercises[1]

    view = card_view(GrammarItem(7, unit.id, exercise.id), remaining=4)

    assert (view.before, view.after) == ("El supermercado ", " cerca de aquí.")
    assert sorted(view.options) == sorted(exercise.options)
    assert view.remaining == 4


def test_the_options_keep_their_order_for_a_card_and_vary_between_cards() -> None:
    unit = get_unit("por_para")
    assert unit is not None
    exercise = unit.exercises[0]

    orders = {
        card_id: card_view(GrammarItem(card_id, unit.id, exercise.id), 0).options
        for card_id in range(1, 40)
    }

    assert card_view(GrammarItem(3, unit.id, exercise.id), 0).options == orders[3]
    assert len(set(orders.values())) == 2


def test_a_typed_exercise_has_no_options() -> None:
    unit = get_unit("ser_estar")
    assert unit is not None

    assert card_view(GrammarItem(1, unit.id, unit.exercises[4].id), 0).options == ()


def test_the_result_names_the_verdict_the_right_word_the_note_and_the_lesson() -> None:
    result = ExerciseResult(
        rating=Rating.AGAIN,
        check=SpanishCheck.WRONG,
        expected="está",
        note="Де щось знаходиться — це estar.",
        unit_id="ser_estar",
    )

    view = result_view(result, " es ")

    assert (view.label, view.tone, view.answer) == ("Ще раз", "again", "es")
    assert (view.expected, view.note) == ("está", "Де щось знаходиться — це estar.")
    assert view.lesson_href == "/grammar/units/ser_estar"
