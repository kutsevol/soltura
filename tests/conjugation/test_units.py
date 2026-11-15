import pytest

from soltura.conjugation.forms import Person, Tense
from soltura.conjugation.units import (
    BASIC_TENSES,
    BLOCK_SIZE,
    EXTRA_TENSES,
    UnitSet,
    introduced_sets,
    next_unit_set,
    parse_unit_key,
    unit_keys,
)

VERBS = ["zzzar", "llover", "ser", "tener"]


def test_the_first_set_is_the_most_frequent_verb_that_can_be_conjugated_in_the_present() -> None:
    assert next_unit_set(VERBS, set()) == UnitSet("ser", Tense.PRESENT)


def test_a_verb_comes_in_every_basic_tense_before_the_next_verb() -> None:
    introduced = {UnitSet("ser", Tense.PRESENT)}
    assert next_unit_set(VERBS, introduced) == UnitSet("ser", Tense.PRETERITE)

    introduced = {UnitSet("ser", tense) for tense in BASIC_TENSES}
    assert next_unit_set(VERBS, introduced) == UnitSet("tener", Tense.PRESENT)


def test_the_conditional_and_the_subjunctive_come_after_the_basic_tenses_of_every_verb_of_the_block() -> (
    None
):
    introduced = {UnitSet(verb, tense) for verb in ("ser", "tener") for tense in BASIC_TENSES}
    assert next_unit_set(VERBS, introduced) == UnitSet("ser", Tense.CONDITIONAL)

    introduced.add(UnitSet("ser", Tense.CONDITIONAL))
    assert next_unit_set(VERBS, introduced) == UnitSet("ser", Tense.SUBJUNCTIVE)

    introduced.add(UnitSet("ser", Tense.SUBJUNCTIVE))
    assert next_unit_set(VERBS, introduced) == UnitSet("tener", Tense.CONDITIONAL)


BLOCK = [
    "hablar", "comer", "vivir", "cantar", "bailar", "beber", "escribir", "abrir", "comprar",
    "vender", "trabajar", "estudiar", "aprender", "correr", "subir", "bajar", "llamar", "mirar",
    "escuchar", "viajar",
]  # fmt: skip


def test_the_next_block_of_verbs_starts_once_the_whole_block_has_every_tense() -> None:
    verbs = [*BLOCK, "preguntar"]
    assert len(BLOCK) == BLOCK_SIZE
    introduced = {UnitSet(verb, tense) for verb in BLOCK for tense in BASIC_TENSES}
    assert next_unit_set(verbs, introduced) == UnitSet("hablar", Tense.CONDITIONAL)

    introduced |= {UnitSet(verb, tense) for verb in BLOCK for tense in EXTRA_TENSES}
    assert next_unit_set(verbs, introduced) == UnitSet("preguntar", Tense.PRESENT)


def test_a_verb_that_cannot_be_conjugated_takes_no_place_in_a_block() -> None:
    verbs = ["zzzar", "llover", *BLOCK, "preguntar"]
    introduced = {UnitSet(verb, tense) for verb in BLOCK for tense in BASIC_TENSES}

    assert next_unit_set(verbs, introduced) == UnitSet("hablar", Tense.CONDITIONAL)


def test_nothing_is_left_once_every_verb_has_every_tense() -> None:
    introduced = {UnitSet(verb, tense) for verb in ("ser", "tener") for tense in Tense}

    assert next_unit_set(VERBS, introduced) is None


def test_a_set_is_six_keys_one_per_person() -> None:
    assert unit_keys(UnitSet("tener", Tense.PRETERITE)) == [
        "tener|preterite|yo",
        "tener|preterite|tu",
        "tener|preterite|el",
        "tener|preterite|nosotros",
        "tener|preterite|vosotros",
        "tener|preterite|ellos",
    ]


def test_a_key_is_read_back_into_its_verb_tense_and_person() -> None:
    assert parse_unit_key("tener|preterite|ellos") == ("tener", Tense.PRETERITE, Person.ELLOS)


@pytest.mark.parametrize(
    "key", [None, "", "tener", "tener|preterite", "tener|pluperfect|yo", "tener|present|usted"]
)
def test_a_key_that_does_not_name_a_form_is_ignored(key: str | None) -> None:
    assert parse_unit_key(key) is None


def test_the_six_persons_of_a_set_count_as_one_introduced_set() -> None:
    keys = [*unit_keys(UnitSet("ser", Tense.PRESENT)), "not a key"]

    assert introduced_sets(keys) == {UnitSet("ser", Tense.PRESENT)}


def test_haber_and_pasar_are_offered_in_their_place_by_frequency() -> None:
    verbs = ["haber", "zzzar", "pasar", "llover", "ser"]
    sets = []
    introduced: set[UnitSet] = set()
    while (next_set := next_unit_set(verbs, introduced)) is not None:
        sets.append(next_set)
        introduced.add(next_set)

    assert [(unit.verb, unit.tense) for unit in sets] == [
        (verb, tense)
        for tenses in (BASIC_TENSES, EXTRA_TENSES)
        for verb in ("haber", "pasar", "ser")
        for tense in tenses
    ]
