import time

import pytest

from soltura.conjugation.forms import (
    IRREGULAR_FORMS,
    REGULAR_LIKE,
    Person,
    Tense,
    conjugate,
    get_conjugator,
)


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


@pytest.mark.parametrize("verb", ["zzzxx", "resultar", "suceder"])
def test_a_verb_without_a_usable_template_returns_nothing(verb: str) -> None:
    assert conjugate(verb, Tense.PRESENT, Person.EL) is None


def test_the_conjugator_loads_in_seconds_without_training_a_model() -> None:
    get_conjugator.cache_clear()
    started = time.perf_counter()

    get_conjugator()

    # Training the fallback model takes about a minute.
    assert time.perf_counter() - started < 10


def _forms(verb: str) -> dict[Tense, list[str | None]]:
    return {tense: [conjugate(verb, tense, person) for person in Person] for tense in Tense}


def test_haber_has_its_own_auxiliary_forms_in_every_tense() -> None:
    assert _forms("haber") == {
        Tense.PRESENT: ["he", "has", "ha", "hemos", "habéis", "han"],
        Tense.PRETERITE: ["hube", "hubiste", "hubo", "hubimos", "hubisteis", "hubieron"],
        Tense.IMPERFECT: ["había", "habías", "había", "habíamos", "habíais", "habían"],
        Tense.FUTURE: ["habré", "habrás", "habrá", "habremos", "habréis", "habrán"],
    }


def test_pasar_takes_the_endings_of_a_regular_ar_verb() -> None:
    assert _forms("pasar") == {
        Tense.PRESENT: ["paso", "pasas", "pasa", "pasamos", "pasáis", "pasan"],
        Tense.PRETERITE: ["pasé", "pasaste", "pasó", "pasamos", "pasasteis", "pasaron"],
        Tense.IMPERFECT: ["pasaba", "pasabas", "pasaba", "pasábamos", "pasabais", "pasaban"],
        Tense.FUTURE: ["pasaré", "pasarás", "pasará", "pasaremos", "pasaréis", "pasarán"],
    }


def test_the_endings_of_pasar_are_those_of_hablar() -> None:
    for tense in Tense:
        for person in Person:
            model = conjugate("hablar", tense, person)
            assert model is not None
            assert conjugate("pasar", tense, person) == "pas" + model.removeprefix("habl")


def test_every_written_out_verb_has_a_form_for_every_tense_and_person() -> None:
    for forms in IRREGULAR_FORMS.values():
        assert set(forms) == set(Tense)
        assert all(len(row) == len(Person) for row in forms.values())


def test_a_regular_model_that_is_not_regular_breaks_loudly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(REGULAR_LIKE, "contar", "tener")

    with pytest.raises(ValueError, match="not regular"):
        conjugate("contar", Tense.PRETERITE, Person.YO)
