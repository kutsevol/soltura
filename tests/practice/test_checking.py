import pytest

from soltura.learner.models import Rating
from soltura.practice.checking import (
    VERDICT_RATING,
    SpanishCheck,
    TranslationVerdict,
    check_spanish,
    judge_translation,
)
from tests.fakes import FakeLLM


@pytest.mark.parametrize(
    ("answer", "expected", "lemma", "check"),
    [
        ("también", "también", "también", SpanishCheck.EXACT),
        ("  Fue. ", "fue", "ir", SpanishCheck.EXACT),
        ("tambien", "también", "también", SpanishCheck.ACCENT_SLIP),
        ("ano", "año", "año", SpanishCheck.ACCENT_SLIP),
        ("tambein", "también", "también", SpanishCheck.TYPO),
        ("ir", "fue", "ir", SpanishCheck.OTHER_FORM),
        ("sal", "sol", "sol", SpanishCheck.WRONG),
        ("perro", "casa", "casa", SpanishCheck.WRONG),
        ("", "fue", "ir", SpanishCheck.WRONG),
    ],
)
def test_check_spanish(answer: str, expected: str, lemma: str, check: SpanishCheck) -> None:
    assert check_spanish(answer, expected, lemma) == check


async def test_a_translation_is_judged_by_the_llm_and_mapped_to_a_rating() -> None:
    llm = FakeLLM()
    llm.answer(TranslationVerdict(verdict="correct", reason="Синонім.", expected="хоча"))

    verdict = await judge_translation(llm, "попри те що", "Aunque", "Aunque llueve, salimos.")

    assert VERDICT_RATING[verdict.verdict] == Rating.GOOD
    assert "Learner's answer: попри те що" in llm.prompts[0]


async def test_an_empty_translation_is_wrong_without_asking_the_llm() -> None:
    llm = FakeLLM()

    verdict = await judge_translation(llm, "  ", "Aunque", "Aunque llueve, salimos.")

    assert verdict.verdict == "wrong"
    assert llm.prompts == []
