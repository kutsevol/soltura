import time

import pytest

from soltura.conjugation.forms import Person, Tense, conjugate, get_conjugator


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
