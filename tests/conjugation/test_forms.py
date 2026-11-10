import time

import pytest

from soltura.conjugation.forms import Person, Tense, conjugate, get_conjugator
from soltura.conjugation.service import regular_endings, verb_forms


@pytest.mark.parametrize(
    ("verb", "tense", "person", "expected"),
    [
        ("ir", Tense.PRETERITE, Person.EL, "fue"),
        ("tener", Tense.PRETERITE, Person.EL, "tuvo"),
        ("pedir", Tense.PRETERITE, Person.EL, "pidió"),
        ("dormir", Tense.PRETERITE, Person.EL, "durmió"),
        ("hacer", Tense.PRETERITE, Person.EL, "hizo"),
        ("hacer", Tense.FUTURE, Person.YO, "haré"),
        ("ser", Tense.PRESENT, Person.YO, "soy"),
        ("ir", Tense.IMPERFECT, Person.NOSOTROS, "íbamos"),
        ("hablar", Tense.PRESENT, Person.VOSOTROS, "habláis"),
        ("comer", Tense.IMPERFECT, Person.ELLOS, "comían"),
    ],
)
def test_irregular_and_regular_forms_are_right(
    verb: str, tense: Tense, person: Person, expected: str
) -> None:
    assert conjugate(verb, tense, person) == expected


def test_every_person_gets_its_own_form() -> None:
    forms = [conjugate("tener", Tense.PRESENT, person) for person in Person]

    assert forms == ["tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"]


@pytest.mark.parametrize("verb", ["zzzxx", "haber", "resultar"])
def test_a_verb_without_a_usable_template_returns_nothing(verb: str) -> None:
    assert conjugate(verb, Tense.PRESENT, Person.EL) is None


def test_the_conjugator_loads_in_seconds_without_training_a_model() -> None:
    get_conjugator.cache_clear()
    started = time.perf_counter()

    get_conjugator()

    # Training the fallback model takes about a minute.
    assert time.perf_counter() - started < 10


def test_a_verbs_table_has_every_tense_in_the_persons_order() -> None:
    forms = verb_forms("ser")

    assert forms is not None
    assert list(forms) == list(Tense)
    assert forms[Tense.PRESENT] == ["soy", "eres", "es", "somos", "sois", "son"]
    assert forms[Tense.PRETERITE][2] == "fue"
    assert all(len(row) == len(Person) for row in forms.values())


def test_a_verb_is_looked_up_in_any_case_and_with_spaces_around() -> None:
    assert verb_forms("  Hablar ") == verb_forms("hablar")


@pytest.mark.parametrize(
    "verb", ["", "x", "dar él", "../etc", "ser;drop", "a" * 31, "zzzar", "llover", "haber"]
)
def test_a_word_that_cannot_be_conjugated_has_no_table(verb: str) -> None:
    assert verb_forms(verb) is None


def test_the_regular_endings_are_taken_off_the_forms_the_trainer_accepts() -> None:
    endings = regular_endings()

    assert endings[Tense.PRESENT]["ar"] == ["o", "as", "a", "amos", "áis", "an"]
    assert endings[Tense.PRESENT]["er"] == ["o", "es", "e", "emos", "éis", "en"]
    assert endings[Tense.PRETERITE]["ir"] == ["í", "iste", "ió", "imos", "isteis", "ieron"]
    assert endings[Tense.IMPERFECT]["ar"] == ["aba", "abas", "aba", "ábamos", "abais", "aban"]
    assert endings[Tense.FUTURE]["er"] == ["é", "ás", "á", "emos", "éis", "án"]
    assert all(
        len(row) == len(Person) for by_ending in endings.values() for row in by_ending.values()
    )
