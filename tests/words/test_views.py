from soltura.words.views import BandView, vocabulary_view
from soltura.words.vocabulary import BandProgress, VocabularyMap


def _view(known: int, learning: int, total: int) -> BandView:
    bands = [BandProgress(1, 250, total, known, learning)]
    return vocabulary_view(VocabularyMap(bands=bands)).bands[0]


def test_one_word_in_a_large_band_is_under_a_percent_not_zero() -> None:
    band = _view(known=0, learning=1, total=230)

    assert band.share_label == "<1%"
    assert "вивчаю <1%" in band.description
    assert "знаю 0%" in band.description
    assert band.learning_width >= 1.0
    assert band.known_width == 0.0


def test_a_band_with_none_of_the_learners_words_is_a_plain_zero() -> None:
    band = _view(known=0, learning=0, total=230)

    assert band.share_label == "0%"
    assert band.learning_width == 0.0


def test_larger_shares_are_rounded_to_whole_percents() -> None:
    assert _view(known=3, learning=0, total=480).share_label == "1%"
    assert _view(known=480, learning=0, total=480).share_label == "100%"
