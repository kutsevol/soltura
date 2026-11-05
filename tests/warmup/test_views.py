import pytest

from soltura.learner.models import KnowledgeType, Rating
from soltura.warmup.service import AnswerResult, WarmupItem
from soltura.warmup.views import card_view, result_view


def _item(sentence: str, target_form: str) -> WarmupItem:
    return WarmupItem(
        card_id=1,
        knowledge_type=KnowledgeType.RECOGNIZE,
        lemma="casa",
        sentence=sentence,
        target_form=target_form,
    )


def test_the_card_splits_the_sentence_around_the_word_and_counts_what_is_left() -> None:
    card = card_view(_item("Mi casa es pequeña.", "casa"), remaining=4)

    assert (card.before, card.target, card.after) == ("Mi ", "casa", " es pequeña.")
    assert card.remaining == 4


def test_a_sentence_without_the_word_is_shown_whole() -> None:
    card = card_view(_item("Una frase.", "casa"), remaining=0)

    assert (card.before, card.target, card.after) == ("Una frase.", "", "")


@pytest.mark.parametrize(
    ("rating", "label"),
    [
        (Rating.GOOD, "Правильно"),
        (Rating.EASY, "Легко"),
        (Rating.HARD, "Майже"),
        (Rating.AGAIN, "Ще раз"),
    ],
)
def test_the_result_names_the_rating_and_trims_the_answer(rating: Rating, label: str) -> None:
    result = AnswerResult(rating=rating, expected="casa", explanation="…")

    view = result_view(result, _item("Mi casa.", "casa"), "  дім ")

    assert (view.label, view.answer) == (label, "дім")
