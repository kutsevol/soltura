from soltura.learner.models import GistResult
from soltura.reading.progress import reading_score
from tests.factories import ReadingTextFactory


def test_no_score_under_three_counted_texts() -> None:
    texts = [ReadingTextFactory.build(gist=GistResult.UNDERSTOOD) for _ in range(2)]

    score = reading_score(texts)

    assert (score.percent, score.counted, score.needed) == (None, 2, 3)


def test_the_score_averages_the_credit_of_each_verdict() -> None:
    texts = [
        ReadingTextFactory.build(gist=GistResult.UNDERSTOOD),
        ReadingTextFactory.build(gist=GistResult.PARTLY),
        ReadingTextFactory.build(gist=GistResult.MISSED),
    ]

    assert reading_score(texts).percent == 50


def test_a_text_below_the_coverage_target_is_left_out() -> None:
    texts = [
        ReadingTextFactory.build(gist=GistResult.UNDERSTOOD),
        ReadingTextFactory.build(gist=GistResult.UNDERSTOOD),
        ReadingTextFactory.build(gist=GistResult.UNDERSTOOD),
        ReadingTextFactory.build(gist=GistResult.MISSED, below_target=True),
    ]

    score = reading_score(texts)

    assert (score.percent, score.counted) == (100, 3)


def test_a_text_without_an_answer_is_not_counted() -> None:
    texts = [ReadingTextFactory.build(gist=None) for _ in range(5)]

    assert reading_score(texts).counted == 0
