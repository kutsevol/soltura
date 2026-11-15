import random
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
from typing import Annotated

from pydantic import StringConstraints

from soltura.conjugation.forms import Person, Tense, conjugate
from soltura.conjugation.units import IMPERSONAL_VERBS, parse_unit_key
from soltura.learner.models import Rating
from soltura.practice.checking import SpanishCheck, check_spanish

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
    tense: Tense


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


def looks_like_verb(verb: str) -> bool:
    # Text from an address or a form must look like a verb before it reaches the library;
    # weather verbs have no personal forms, though the library conjugates them in full.
    return bool(_INFINITIVE.fullmatch(verb)) and verb not in IMPERSONAL_VERBS


def verb_forms(verb: str) -> dict[Tense, list[str]] | None:
    word = verb.strip().lower()
    if not looks_like_verb(word):
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
            # The future and the conditional are built on the whole infinitive, the other
            # tenses on the stem.
            stem = verb if tense in (Tense.FUTURE, Tense.CONDITIONAL) else verb[:-2]
            forms = [conjugate(verb, tense, person) for person in Person]
            # A model verb that stops being regular must break here, not show a wrong table.
            if any(form is None or not form.startswith(stem) for form in forms):
                raise ValueError(f"{verb} is not regular in the {tense} tense")
            endings[tense][verb[-2:]] = [str(form).removeprefix(stem) for form in forms]
    return endings


@dataclass(frozen=True)
class PracticeItem:
    # The item comes back from a page, so its verb is checked where the item is read.
    verb: Annotated[str, StringConstraints(max_length=30, pattern=r"^[a-zñáéíóúü]+$")]
    tense: Tense
    person: Person


def practice_queue(verb: str, tenses: list[Tense], rng: random.Random) -> list[PracticeItem] | None:
    # Every person of each chosen tense, once, in a mixed order; nothing is scheduled or stored.
    word = verb.strip().lower()
    if not verb_forms(word):
        return None
    items = [
        PracticeItem(word, tense, person) for tense in dict.fromkeys(tenses) for person in Person
    ]
    rng.shuffle(items)
    return items


def check_practice(item: PracticeItem, answer: str) -> ConjugationResult:
    expected = conjugate(item.verb, item.tense, item.person) if looks_like_verb(item.verb) else None
    if expected is None:
        raise ValueError(f"{item.verb} cannot be conjugated in the {item.tense} tense")
    check = check_spanish(answer, expected, item.verb)
    return ConjugationResult(
        rating=CONJUGATION_RATING[check],
        check=check,
        expected=expected,
        verb=item.verb,
        tense=item.tense,
    )
