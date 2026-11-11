import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta

from soltura.conjugation.forms import Person, Tense, conjugate
from soltura.conjugation.units import IMPERSONAL_VERBS, parse_unit_key
from soltura.learner.models import Rating
from soltura.practice.checking import SpanishCheck

SESSION_SIZE = 18
# A rolling window, so the cap needs no time zone.
NEW_SETS_WINDOW = timedelta(hours=24)

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
class ConjugationSession:
    items: list[ConjugationItem]
    capped: bool


@dataclass(frozen=True)
class ConjugationResult:
    rating: Rating
    check: SpanishCheck
    expected: str
    verb: str


RECENT_ANSWERS = 200
MIN_ANSWERS = 10


@dataclass(frozen=True)
class TenseAccuracy:
    tense: Tense
    answers: int
    right: int


def tense_accuracy(answers: Iterable[tuple[Rating, str | None]]) -> list[TenseAccuracy]:
    answered = Counter[Tense]()
    right = Counter[Tense]()
    for rating, key in answers:
        parsed = parse_unit_key(key)
        if parsed is None:
            continue
        answered[parsed[1]] += 1
        if rating in (Rating.GOOD, Rating.EASY):
            right[parsed[1]] += 1
    return [
        TenseAccuracy(tense, answered[tense], right[tense]) for tense in Tense if answered[tense]
    ]


# The regular verb of each ending: its endings, taken off the forms the trainer accepts,
# are the regular endings, so the table cannot disagree with an answer that is accepted.
MODEL_VERBS = ("hablar", "comer", "vivir")
# An infinitive: a stem and -ar, -er, -ir or -ír (oír, freír), or ir itself. The library
# also conjugates reflexive forms such as lavarse, with the pronoun inside the form.
_INFINITIVE = re.compile(r"(?:[a-zñáéíóúü]{1,28}(?:ar|er|ir|ír)|ir)")


def verb_forms(verb: str) -> dict[Tense, list[str]] | None:
    # The verb comes from an address, so it must look like a word before it reaches the library.
    word = verb.strip().lower()
    # Weather verbs have no personal forms, though the library conjugates them in full.
    if not _INFINITIVE.fullmatch(word) or word in IMPERSONAL_VERBS:
        return None
    forms: dict[Tense, list[str]] = {}
    for tense in Tense:
        row = [conjugate(word, tense, person) for person in Person]
        if any(form is None for form in row):
            return None
        forms[tense] = [form for form in row if form is not None]
    return forms


def regular_endings() -> dict[Tense, dict[str, list[str]]]:
    endings: dict[Tense, dict[str, list[str]]] = {}
    for tense in Tense:
        endings[tense] = {}
        for verb in MODEL_VERBS:
            # The future is built on the whole infinitive, the other tenses on the stem.
            stem = verb if tense == Tense.FUTURE else verb[:-2]
            forms = [conjugate(verb, tense, person) for person in Person]
            # A model verb that stops being regular must break here, not show a wrong table.
            if any(form is None or not form.startswith(stem) for form in forms):
                raise ValueError(f"{verb} is not regular in the {tense} tense")
            endings[tense][verb[-2:]] = [str(form).removeprefix(stem) for form in forms]
    return endings
