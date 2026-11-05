from dataclasses import dataclass

from soltura.conjugation.forms import Person, Tense
from soltura.conjugation.service import ConjugationItem, ConjugationResult
from soltura.learner.models import Rating
from soltura.practice.checking import SpanishCheck
from soltura.practice.views import RATING_LABEL

TENSE_LABEL = {
    Tense.PRESENT: "теперішній час · presente",
    Tense.PRETERITE: "минулий звершений · pretérito indefinido",
    Tense.IMPERFECT: "минулий тривалий · pretérito imperfecto",
    Tense.FUTURE: "майбутній час · futuro",
}

PRONOUN_LABEL = {
    Person.YO: "yo",
    Person.TU: "tú",
    Person.EL: "él / ella / usted",
    Person.NOSOTROS: "nosotros",
    Person.VOSOTROS: "vosotros",
    Person.ELLOS: "ellos / ellas / ustedes",
}


@dataclass(frozen=True)
class CardView:
    card_id: int
    verb: str
    tense: str
    pronoun: str
    remaining: int


@dataclass(frozen=True)
class ResultView:
    label: str
    tone: str
    answer: str
    explanation: str
    expected: str | None


def card_view(item: ConjugationItem, remaining: int) -> CardView:
    return CardView(
        card_id=item.card_id,
        verb=item.verb,
        tense=TENSE_LABEL[item.tense],
        pronoun=PRONOUN_LABEL[item.person],
        remaining=remaining,
    )


def _explanation(check: SpanishCheck) -> str:
    return {
        SpanishCheck.EXACT: "Правильно.",
        SpanishCheck.ACCENT_SLIP: "Майже: перевірте наголос.",
        SpanishCheck.TYPO: "Одна буква змінює форму.",
        SpanishCheck.OTHER_FORM: "Потрібна особова форма, не інфінітив.",
        SpanishCheck.WRONG: "Це не та форма.",
    }[check]


def result_view(result: ConjugationResult, answer: str) -> ResultView:
    return ResultView(
        label=RATING_LABEL[result.rating],
        tone=result.rating.value,
        answer=answer.strip(),
        explanation=_explanation(result.check),
        expected=None if result.rating == Rating.GOOD else result.expected,
    )
