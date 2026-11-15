import pytest

from soltura.conjugation.forms import Person, Tense, conjugate
from soltura.conjugation.patterns import PATTERNS, pattern_notes, regular_form

REFERENCE = {
    "pensar": ["stem_e_ie"],
    "poder": ["stem_o_ue", "strong_preterite", "short_future"],
    "pedir": ["stem_e_i", "raised_preterite"],
    "jugar": ["stem_u_ue", "spelling_yo"],
    "tener": ["stem_e_ie", "go_yo", "strong_preterite", "short_future"],
    "conocer": ["zco_yo"],
    "buscar": ["spelling_yo"],
    "empezar": ["stem_e_ie", "spelling_yo"],
    "leer": ["y_preterite"],
    "ser": ["strong_preterite", "irregular_imperfect"],
    "dormir": ["stem_o_ue", "raised_preterite"],
    "oír": ["go_yo", "y_preterite"],
    "seguir": ["stem_e_i", "raised_preterite"],
    "llegar": ["spelling_yo"],
    "salir": ["go_yo", "short_future"],
    "ver": ["irregular_imperfect"],
    "dar": [],
    "reír": ["stem_e_i", "raised_preterite"],
    "sonreír": ["stem_e_i", "raised_preterite"],
    "traer": ["go_yo", "strong_preterite"],
    "prever": ["irregular_imperfect"],
}


@pytest.mark.parametrize("verb", list(REFERENCE))
def test_a_verb_gets_the_patterns_its_forms_show(verb: str) -> None:
    assert [note.pattern.id for note in pattern_notes(verb)] == REFERENCE[verb]


@pytest.mark.parametrize("verb", ["hablar", "comer", "vivir", "pasar", "cantar", "beber"])
def test_a_regular_verb_has_no_pattern(verb: str) -> None:
    assert pattern_notes(verb) == []


@pytest.mark.parametrize("verb", list(REFERENCE) + ["hacer", "decir", "venir", "conducir", "dar"])
def test_every_example_of_a_note_is_a_form_the_trainer_accepts(verb: str) -> None:
    for note in pattern_notes(verb):
        for example in note.examples:
            accepted = {conjugate(verb, example.tense, person) for person in Person}
            assert example.forms and set(example.forms) <= accepted
            assert example.tense in note.pattern.tenses


def test_the_examples_of_a_stem_change_leave_out_the_forms_that_keep_the_stem() -> None:
    [note] = pattern_notes("pensar")

    assert [example.forms for example in note.examples] == [
        ["pienso", "piensas", "piensa", "piensan"]
    ]


def test_with_a_tense_only_the_patterns_that_touch_it_are_listed() -> None:
    ids = {tense: [note.pattern.id for note in pattern_notes("tener", tense)] for tense in Tense}

    assert ids[Tense.PRESENT] == ["stem_e_ie", "go_yo"]
    assert ids[Tense.PRETERITE] == ["strong_preterite"]
    assert ids[Tense.FUTURE] == ids[Tense.CONDITIONAL] == ["short_future"]
    assert ids[Tense.IMPERFECT] == ids[Tense.SUBJUNCTIVE] == []


def test_the_future_of_a_verb_on_ir_with_an_accent_is_regular() -> None:
    assert regular_form("oír", Tense.FUTURE, Person.YO) == "oiré"
    assert conjugate("oír", Tense.FUTURE, Person.YO) == "oiré"


def test_every_pattern_has_its_own_id_a_title_and_a_rule() -> None:
    assert len({pattern.id for pattern in PATTERNS}) == len(PATTERNS)
    assert all(pattern.title and pattern.rule and pattern.tenses for pattern in PATTERNS)


def test_the_spelling_of_a_stem_change_is_followed_in_the_form_of_yo_and_in_a_vowel_stem() -> None:
    [seguir_present, _] = pattern_notes("seguir")
    [reir_present, reir_preterite] = pattern_notes("reír")

    assert seguir_present.examples[0].forms == ["sigo", "sigues", "sigue", "siguen"]
    assert reir_present.examples[0].forms == ["río", "ríes", "ríe", "ríen"]
    assert reir_preterite.examples[0].forms == ["rió", "rieron"]


def test_a_verb_that_only_takes_the_endings_of_another_conjugation_is_not_a_strong_preterite() -> (
    None
):
    assert conjugate("dar", Tense.PRETERITE, Person.YO) == "di"
    assert [note.pattern.id for note in pattern_notes("dar", Tense.PRETERITE)] == []
    assert [note.pattern.id for note in pattern_notes("ver", Tense.PRETERITE)] == []
