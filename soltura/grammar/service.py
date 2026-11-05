from dataclasses import dataclass

from soltura.grammar.units import Exercise
from soltura.learner.models import Rating
from soltura.practice.checking import SpanishCheck, check_spanish

SESSION_SIZE = 12

# The word is what is being learned: a missing accent is a slip, anything else is
# another word and does not pass.
GRAMMAR_RATING = {
    SpanishCheck.EXACT: Rating.GOOD,
    SpanishCheck.ACCENT_SLIP: Rating.HARD,
    SpanishCheck.TYPO: Rating.AGAIN,
    SpanishCheck.OTHER_FORM: Rating.AGAIN,
    SpanishCheck.WRONG: Rating.AGAIN,
}


@dataclass(frozen=True)
class GrammarItem:
    card_id: int
    unit_id: str
    exercise_id: str


@dataclass(frozen=True)
class ExerciseResult:
    rating: Rating
    check: SpanishCheck
    expected: str
    note: str
    unit_id: str


def check_exercise(exercise: Exercise, answer: str) -> SpanishCheck:
    if exercise.is_choice:
        return SpanishCheck.EXACT if answer == exercise.answer else SpanishCheck.WRONG
    return check_spanish(answer, exercise.answer, exercise.answer)
