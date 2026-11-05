import pytest

from soltura.grammar.service import GRAMMAR_RATING, check_exercise
from soltura.grammar.units import Exercise
from soltura.learner.models import Rating
from soltura.practice.checking import SpanishCheck

CHOICE = Exercise(
    id="e1",
    sentence="Mi madre ___ de Kyiv.",
    translation="Моя мама з Києва.",
    options=("es", "está"),
    answer="es",
    note="Походження — це ser.",
)
GAP = CHOICE.model_copy(update={"options": (), "answer": "está"})


@pytest.mark.parametrize(
    ("exercise", "answer", "check"),
    [
        (CHOICE, "es", SpanishCheck.EXACT),
        (CHOICE, "está", SpanishCheck.WRONG),
        (CHOICE, "", SpanishCheck.WRONG),
        (GAP, "está", SpanishCheck.EXACT),
        (GAP, " Está. ", SpanishCheck.EXACT),
        (GAP, "esta", SpanishCheck.ACCENT_SLIP),
        (GAP, "es", SpanishCheck.WRONG),
        (GAP, "", SpanishCheck.WRONG),
    ],
)
def test_an_answer_is_checked_against_the_stored_one(
    exercise: Exercise, answer: str, check: SpanishCheck
) -> None:
    assert check_exercise(exercise, answer) == check


def test_only_the_exact_word_is_good_and_only_a_missing_accent_is_hard() -> None:
    assert GRAMMAR_RATING[SpanishCheck.EXACT] == Rating.GOOD
    assert GRAMMAR_RATING[SpanishCheck.ACCENT_SLIP] == Rating.HARD
    assert {
        GRAMMAR_RATING[check]
        for check in (SpanishCheck.TYPO, SpanishCheck.OTHER_FORM, SpanishCheck.WRONG)
    } == {Rating.AGAIN}
