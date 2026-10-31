import pytest

from soltura.language.coverage import Coverage, measure_coverage, words_to_replace
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


def _coverage(total: int, unknown_counts: dict[str, int]) -> Coverage:
    unknown = sum(unknown_counts.values())
    return Coverage(
        ratio=(total - unknown) / total,
        total_words=total,
        unknown_lemmas=list(unknown_counts),
        unknown_counts=unknown_counts,
    )


def test_only_the_rarest_excess_words_are_replaced() -> None:
    # 40 words allow 2 unknown at 95%; 3 are unknown, so one goes: the unranked one.
    coverage = _coverage(40, {"nieto": 1, "bicicleta": 1, "arrendatario": 1})

    chosen = words_to_replace(coverage, {"nieto": 3000, "bicicleta": 2500}, target=0.95)

    assert chosen == ["arrendatario"]


def test_a_text_within_the_budget_keeps_its_unknown_words() -> None:
    coverage = _coverage(40, {"nieto": 1, "bicicleta": 1})

    assert words_to_replace(coverage, {}, target=0.95) == []


def test_a_repeated_rare_word_counts_every_time_it_appears() -> None:
    # 20 words allow 1 unknown; "fianza" three times is the excess on its own.
    coverage = _coverage(20, {"fianza": 3, "nieto": 1})

    assert words_to_replace(coverage, {"fianza": 9000, "nieto": 3000}, target=0.95) == ["fianza"]
