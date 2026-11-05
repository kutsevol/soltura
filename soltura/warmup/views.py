from dataclasses import dataclass

from soltura.practice.text import split_around
from soltura.practice.views import RATING_LABEL
from soltura.warmup.service import AnswerResult, WarmupItem


@dataclass(frozen=True)
class CardView:
    item: WarmupItem
    before: str
    target: str
    after: str
    remaining: int


@dataclass(frozen=True)
class ResultView:
    result: AnswerResult
    label: str
    answer: str
    item: WarmupItem


def card_view(item: WarmupItem, remaining: int) -> CardView:
    before, target, after = split_around(item.sentence, item.target_form) or (
        item.sentence,
        "",
        "",
    )
    return CardView(item=item, before=before, target=target, after=after, remaining=remaining)


def result_view(result: AnswerResult, item: WarmupItem, answer: str) -> ResultView:
    return ResultView(
        result=result, label=RATING_LABEL[result.rating], answer=answer.strip(), item=item
    )
