from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from soltura.grammar.units import SEPARATOR, Exercise, GrammarUnit, all_units
from soltura.learner.models import Rating
from soltura.learner.repository import CardProgress
from soltura.practice.checking import SpanishCheck, check_spanish

SESSION_SIZE = 12

# An exercise counts as in memory once FSRS expects the learner to recall it for a week.
SOLID_STABILITY_DAYS = 7

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


@dataclass(frozen=True)
class UnitProgress:
    unit: GrammarUnit
    answers: int
    right: int
    solid: int
    next_due: datetime


@dataclass(frozen=True)
class GrammarProgress:
    units: list[UnitProgress]
    not_started: int


def build_progress(cards: Iterable[CardProgress]) -> GrammarProgress:
    # A unit is listed as soon as one of its exercises has a card, in teaching order.
    by_unit: dict[str, list[CardProgress]] = defaultdict(list)
    for card in cards:
        by_unit[card.unit_key.split(SEPARATOR)[0]].append(card)
    units = [
        UnitProgress(
            unit=unit,
            answers=sum(card.answers for card in by_unit[unit.id]),
            right=sum(card.right for card in by_unit[unit.id]),
            solid=sum(
                card.stability is not None and card.stability >= SOLID_STABILITY_DAYS
                for card in by_unit[unit.id]
            ),
            next_due=min(card.due for card in by_unit[unit.id]),
        )
        for unit in all_units()
        if unit.id in by_unit
    ]
    return GrammarProgress(units=units, not_started=len(all_units()) - len(units))
