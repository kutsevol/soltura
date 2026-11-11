import pytest

from soltura.conjugation.forms import Person, Tense
from soltura.conjugation.service import TenseAccuracy, regular_endings, tense_accuracy, verb_forms
from soltura.learner.models import Rating


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
    "verb",
    ["", "x", "dar él", "../etc", "ser;drop", "a" * 31, "zzzar", "llover", "resultar"]
    + ["ar", "qqqir", "lavarse", "irse", "ñandar", "hab lar"],
)
def test_a_word_that_cannot_be_conjugated_has_no_table(verb: str) -> None:
    assert verb_forms(verb) is None


def test_the_regular_endings_are_the_whole_table_of_the_three_conjugations() -> None:
    assert regular_endings() == {
        Tense.PRESENT: {
            "ar": ["o", "as", "a", "amos", "áis", "an"],
            "er": ["o", "es", "e", "emos", "éis", "en"],
            "ir": ["o", "es", "e", "imos", "ís", "en"],
        },
        Tense.PRETERITE: {
            "ar": ["é", "aste", "ó", "amos", "asteis", "aron"],
            "er": ["í", "iste", "ió", "imos", "isteis", "ieron"],
            "ir": ["í", "iste", "ió", "imos", "isteis", "ieron"],
        },
        Tense.IMPERFECT: {
            "ar": ["aba", "abas", "aba", "ábamos", "abais", "aban"],
            "er": ["ía", "ías", "ía", "íamos", "íais", "ían"],
            "ir": ["ía", "ías", "ía", "íamos", "íais", "ían"],
        },
        Tense.FUTURE: {
            "ar": ["é", "ás", "á", "emos", "éis", "án"],
            "er": ["é", "ás", "á", "emos", "éis", "án"],
            "ir": ["é", "ás", "á", "emos", "éis", "án"],
        },
    }


def test_the_accuracy_of_a_tense_counts_good_and_easy_answers_as_right() -> None:
    answers = [
        (Rating.GOOD, "ser|present|yo"),
        (Rating.EASY, "ser|present|tu"),
        (Rating.HARD, "ser|present|el"),
        (Rating.AGAIN, "ser|present|nosotros"),
        (Rating.GOOD, "ser|future|yo"),
    ]

    assert tense_accuracy(answers) == [
        TenseAccuracy(Tense.PRESENT, answers=4, right=2),
        TenseAccuracy(Tense.FUTURE, answers=1, right=1),
    ]


def test_a_tense_with_no_answers_is_left_out_and_the_rest_follow_the_order_of_tenses() -> None:
    answers = [(Rating.GOOD, "ser|imperfect|yo"), (Rating.GOOD, "ser|preterite|yo")]

    assert [item.tense for item in tense_accuracy(answers)] == [Tense.PRETERITE, Tense.IMPERFECT]


@pytest.mark.parametrize("key", [None, "", "ser", "ser|conditional|yo", "ser|present|you"])
def test_an_answer_whose_card_names_no_form_is_not_counted(key: str | None) -> None:
    assert tense_accuracy([(Rating.GOOD, key)]) == []
