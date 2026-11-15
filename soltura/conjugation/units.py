from collections.abc import Iterable, Iterator
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


# A learner meets the four basic tenses before the conditional and the subjunctive, in blocks
# of the most frequent verbs: all the basic tenses of a block, then the other two for the
# same verbs, then the next block. Otherwise the subjunctive of ser would come before the
# present of estar.
BASIC_TENSES = (Tense.PRESENT, Tense.PRETERITE, Tense.IMPERFECT, Tense.FUTURE)
EXTRA_TENSES = (Tense.CONDITIONAL, Tense.SUBJUNCTIVE)
BLOCK_SIZE = 20


def _blocks(verbs: Iterable[str]) -> Iterator[list[str]]:
    block: list[str] = []
    for verb in verbs:
        # A verb that has no personal forms or that the library cannot conjugate in the present
        # takes no place: it would otherwise get a conditional without its basic tenses.
        if verb in IMPERSONAL_VERBS or not all(
            conjugate(verb, Tense.PRESENT, person) for person in Person
        ):
            continue
        block.append(verb)
        if len(block) == BLOCK_SIZE:
            yield block
            block = []
    if block:
        yield block


def next_unit_set(verbs: Iterable[str], introduced: set[UnitSet]) -> UnitSet | None:
    # Verbs arrive by frequency. In a block, each verb comes in every basic tense before the
    # next verb, and then in the other tenses.
    for block in _blocks(verbs):
        for tenses in (BASIC_TENSES, EXTRA_TENSES):
            for verb in block:
                for tense in tenses:
                    candidate = UnitSet(verb, tense)
                    if candidate in introduced:
                        continue
                    if all(conjugate(verb, tense, person) for person in Person):
                        return candidate
                    # In the basic pass a verb that cannot take a tense is left there; the
                    # conditional and the subjunctive do not depend on each other.
                    if tenses is BASIC_TENSES:
                        break
    return None
