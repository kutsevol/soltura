from dataclasses import dataclass

from soltura.conjugation.forms import Person, Tense
from soltura.learner.models import Rating
from soltura.practice.checking import SpanishCheck

SESSION_SIZE = 18

# The ending is what is being learned: a missing accent is a slip, a changed letter is
# another form (tuvieron against tuvieran) and does not pass.
CONJUGATION_RATING = {
    SpanishCheck.EXACT: Rating.GOOD,
    SpanishCheck.ACCENT_SLIP: Rating.HARD,
    SpanishCheck.TYPO: Rating.AGAIN,
    SpanishCheck.OTHER_FORM: Rating.AGAIN,
    SpanishCheck.WRONG: Rating.AGAIN,
}


@dataclass(frozen=True)
class ConjugationItem:
    card_id: int
    verb: str
    tense: Tense
    person: Person


@dataclass(frozen=True)
class ConjugationResult:
    rating: Rating
    check: SpanishCheck
    expected: str
