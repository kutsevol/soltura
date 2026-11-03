from collections.abc import Iterable
from dataclasses import dataclass

from soltura.conjugation.forms import Person, Tense, conjugate

SEPARATOR = "|"

# Weather verbs have no personal forms, though verbecc conjugates them in full.
IMPERSONAL_VERBS = frozenset(
    {
        "amanecer",
        "anochecer",
        "atardecer",
        "chispear",
        "granizar",
        "helar",
        "llover",
        "lloviznar",
        "nevar",
        "relampaguear",
        "tronar",
    }
)


@dataclass(frozen=True)
class UnitSet:
    verb: str
    tense: Tense


def unit_key(verb: str, tense: Tense, person: Person) -> str:
    return SEPARATOR.join((verb, tense, person))


def unit_keys(unit_set: UnitSet) -> list[str]:
    return [unit_key(unit_set.verb, unit_set.tense, person) for person in Person]


def parse_unit_key(key: str | None) -> tuple[str, Tense, Person] | None:
    parts = (key or "").split(SEPARATOR)
    if len(parts) != 3:
        return None
    verb, tense, person = parts
    try:
        return verb, Tense(tense), Person(person)
    except ValueError:
        return None


def introduced_sets(keys: Iterable[str]) -> set[UnitSet]:
    sets: set[UnitSet] = set()
    for key in keys:
        parsed = parse_unit_key(key)
        if parsed is not None:
            sets.add(UnitSet(parsed[0], parsed[1]))
    return sets


def next_unit_set(verbs: Iterable[str], introduced: set[UnitSet]) -> UnitSet | None:
    # Verbs arrive by frequency, and each verb's tenses in teaching order: the learner
    # meets one verb in every tense before the next verb.
    for verb in verbs:
        if verb in IMPERSONAL_VERBS:
            continue
        for tense in Tense:
            candidate = UnitSet(verb, tense)
            if candidate in introduced:
                continue
            if all(conjugate(verb, tense, person) for person in Person):
                return candidate
            break
    return None
