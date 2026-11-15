import pytest

from soltura.reading.views import MAX_SHOWN_TRANSLATION, short_translation, split_for_reading


def test_split_for_reading_keeps_each_word_with_its_sentence() -> None:
    paragraphs = split_for_reading("Ayer fue al médico. ¿Qué te dijo?\n\nNada, todo bien.")

    sentences = [["".join(s.text for s in sentence).strip() for sentence in p] for p in paragraphs]
    assert sentences == [["Ayer fue al médico.", "¿Qué te dijo?"], ["Nada, todo bien."]]
    words = [s.text for s in paragraphs[0][1] if s.is_word]
    assert words == ["Qué", "te", "dijo"]


def test_a_word_carries_the_translation_that_starts_where_it_starts() -> None:
    text = "Ayer fue al médico.\n\nNada... ... Sí, vamos al médico."
    first, second = text.index("médico"), text.rindex("médico")

    paragraphs = split_for_reading(
        text, {first: "лікар", second: "лікар", text.index("vamos"): "йти"}
    )

    shown = [
        (segment.text, segment.translation)
        for paragraph in paragraphs
        for sentence in paragraph
        for segment in sentence
        if segment.translation
    ]
    assert shown == [("médico", "лікар"), ("vamos", "йти"), ("médico", "лікар")]


def test_a_translation_at_a_position_that_is_not_a_word_start_is_not_shown() -> None:
    text = "Ayer fue al médico."

    paragraphs = split_for_reading(text, {text.index("médico") + 1: "лікар", 1: "вчора"})

    assert all(segment.translation is None for sentence in paragraphs[0] for segment in sentence)


def test_without_translations_no_word_has_one() -> None:
    paragraphs = split_for_reading("Ayer fue al médico.")

    assert all(segment.translation is None for segment in paragraphs[0][0])


@pytest.mark.parametrize(
    ("given", "shown"),
    [
        ("компанія, підприємство", "компанія"),
        ("лікар; доктор", "лікар"),
        ("бути (постійно)", "бути"),
        ("  онук  ", "онук"),
        ("а" * 40, "а" * (MAX_SHOWN_TRANSLATION - 1) + "…"),
    ],
)
def test_the_line_above_a_word_is_its_first_meaning_and_short(given: str, shown: str) -> None:
    assert short_translation(given) == shown
