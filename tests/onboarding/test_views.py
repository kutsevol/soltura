from soltura.onboarding.service import BANDS, BandScore, PlacementResult, WordResult
from soltura.onboarding.views import explanation


def _bands(*correct: int) -> list[BandScore]:
    return [BandScore(band, BANDS[band][1], right, 8) for band, right in enumerate(correct)]


def _right_word(band: int) -> WordResult:
    return WordResult(
        band=band,
        lemma="casa",
        sentence="Mi casa.",
        target_form="casa",
        answer="дім",
        verdict="correct",
        reason="",
        expected="дім",
    )


def test_a_broken_run_names_the_band_it_broke_on_and_the_right_words_above_it() -> None:
    result = PlacementResult(known_rank=250, bands=_bands(6, 4, 2), words=[_right_word(2)])

    lines = explanation(result)

    assert lines[0] == "Питань: 24, правильних відповідей: 12."
    assert "Серія пройдених груп обірвалась на групі до 500: 4 з 8." in lines
    assert any("рідших групах: 1" in line for line in lines)
    assert any("Тест зупинився після групи до 1000" in line for line in lines)


def test_a_learner_who_passed_every_band_has_nothing_to_explain_but_the_total() -> None:
    result = PlacementResult(known_rank=6000, bands=_bands(*[8] * 8))

    lines = explanation(result)

    assert "Усі групи, про які питали, пройдені." in lines
    assert not any("обірвалась" in line or "зупинився" in line for line in lines)


def test_a_run_without_answers_does_not_claim_right_words_above_the_rank() -> None:
    result = PlacementResult(known_rank=250, bands=_bands(5, 4, 2, 3, 4, 4, 2, 2))

    assert not any("рідших групах" in line for line in explanation(result))
