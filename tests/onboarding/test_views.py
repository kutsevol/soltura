from soltura.language.frequency import BANDS
from soltura.onboarding.service import (
    BandScore,
    LearnOutcome,
    MissedSummary,
    PlacementItem,
    PlacementResult,
    WordResult,
)
from soltura.onboarding.views import card_view, explanation, learn_view, result_view
from soltura.use_cases.onboarding import ResultScreen
from soltura.words.vocabulary import BandProgress, VocabularyMap


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


def _item(band: int, sentence: str, target: str) -> PlacementItem:
    return PlacementItem(band=band, lemma=target, sentence=sentence, target_form=target)


def test_the_card_splits_the_sentence_around_the_word() -> None:
    queue = [_item(0, "Mi casa es pequeña.", "casa")]

    card = card_view(queue, answered=[])

    assert (card.before, card.target, card.after) == ("Mi ", "casa", " es pequeña.")
    assert (card.position, card.total) == (1, 1)


def test_a_sentence_without_the_word_is_shown_whole() -> None:
    card = card_view([_item(0, "Una frase.", "casa")], answered=[])

    assert (card.before, card.target, card.after) == ("Una frase.", "", "")


def test_the_card_knows_when_it_is_the_last_word_of_a_band() -> None:
    queue = [
        _item(0, "Mi casa.", "casa"),
        _item(0, "Mi perro.", "perro"),
        _item(1, "Mi pan.", "pan"),
    ]

    assert not card_view(queue, []).checking
    assert card_view(queue[1:], answered=[queue[0]]).checking
    assert card_view(queue[2:], answered=queue[:2]).checking
    assert card_view(queue[2:], answered=queue[:2]).position == 3


def test_the_result_view_collects_the_strings_the_screen_needs() -> None:
    result = PlacementResult(known_rank=250, bands=_bands(6, 4, 2))
    screen = ResultScreen(
        result=result,
        vocabulary=VocabularyMap(bands=[BandProgress(1, 250, 10, 4, 1)]),
        reading_range=250,
        missed=MissedSummary(total=20, batch=15),
    )

    view = result_view(screen)

    assert view.known_summary == "Знаю слів: 4 з 10"
    assert view.explanation == explanation(result)
    assert (view.reading_range, view.missed_total, view.missed_batch) == (250, 20, 15)


def test_the_learn_view_reports_what_was_added() -> None:
    view = learn_view(LearnOutcome(added=15, missed=MissedSummary(total=5, batch=5)))

    assert (view.added, view.missed_total, view.missed_batch) == (15, 5, 5)
