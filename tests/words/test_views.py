from datetime import UTC, datetime, timedelta

from soltura.words.views import BandView, due_label, vocabulary_view, words_view
from soltura.words.vocabulary import BandProgress, VocabularyMap

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


def test_a_card_due_now_or_earlier_reads_now_and_a_later_one_its_date() -> None:
    assert due_label(NOW, NOW) == "зараз"
    assert due_label(NOW - timedelta(days=1), NOW) == "зараз"
    assert due_label(NOW + timedelta(days=3), NOW) == "03.11.2026"


def test_the_words_view_trims_the_search_it_shows() -> None:
    view = words_view([], "  nieto ", NOW)

    assert (view.search, view.now) == ("nieto", NOW)


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
