import pytest

from soltura.language.coverage import measure_coverage
from soltura.language.nlp import analyze


def test_coverage_counts_running_words() -> None:
    # comprar, kilo, de, pan, pan, y, más, pan: 8 words; the number and punctuation do not count.
    tokens = analyze("Compré 3 kilos de pan, pan y más pan.")

    coverage = measure_coverage(tokens, known_lemmas={"comprar", "de", "y", "más"})

    assert coverage.total_words == 8
    assert coverage.ratio == pytest.approx(4 / 8)
    assert coverage.unknown_lemmas == ["pan", "kilo"]


def test_coverage_of_a_fully_known_text_is_one() -> None:
    tokens = analyze("Ayer fue al médico.")

    coverage = measure_coverage(tokens, known_lemmas={"ayer", "ser", "al", "médico"})

    assert coverage.ratio == 1.0
    assert coverage.unknown_lemmas == []


def test_coverage_of_an_empty_text_is_one() -> None:
    coverage = measure_coverage([], known_lemmas=set())

    assert coverage.ratio == 1.0
    assert coverage.total_words == 0
