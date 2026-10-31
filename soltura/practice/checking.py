import re
import unicodedata
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from soltura.learner.models import Rating
from soltura.llm.client import LLMClient

JUDGE_SYSTEM = (
    "You check a Ukrainian-speaking learner's translation of one Spanish word. You get the "
    "word, the sentence it is used in, and the learner's answer in Ukrainian. Judge the meaning "
    "in this sentence, not the spelling or the grammatical form of the answer. 'correct' when "
    "the answer means the word as used here, synonyms included; 'partly' when it names a "
    "related or more general meaning; 'wrong' otherwise. Give a one-line reason in Ukrainian "
    "and the expected meaning."
)


class SpanishCheck(StrEnum):
    EXACT = "exact"
    ACCENT_SLIP = "accent_slip"
    TYPO = "typo"
    OTHER_FORM = "other_form"
    WRONG = "wrong"


class TranslationVerdict(BaseModel):
    verdict: Literal["correct", "partly", "wrong"] = Field(
        description="Whether the answer means the word as it is used in the sentence"
    )
    reason: str = Field(description="One line in Ukrainian explaining the verdict")
    expected: str = Field(description="The word's meaning in this sentence, in Ukrainian")


SPANISH_RATING = {
    SpanishCheck.EXACT: Rating.GOOD,
    SpanishCheck.ACCENT_SLIP: Rating.HARD,
    SpanishCheck.TYPO: Rating.HARD,
    SpanishCheck.OTHER_FORM: Rating.HARD,
    SpanishCheck.WRONG: Rating.AGAIN,
}

VERDICT_RATING = {"correct": Rating.GOOD, "partly": Rating.HARD, "wrong": Rating.AGAIN}

MIN_LENGTH_FOR_TYPO = 4


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().strip(".,;:!?¡¿«»\"'").lower())


def strip_accents(text: str) -> str:
    # NFD splits "á" and "ñ" into a letter plus a combining mark; dropping the marks
    # turns "también" into "tambien" and "año" into "ano".
    return "".join(
        char for char in unicodedata.normalize("NFD", text) if not unicodedata.combining(char)
    )


def _within_one_edit(answer: str, expected: str) -> bool:
    # One substitution, insertion, deletion or swap of two neighbouring letters.
    if answer == expected:
        return True
    if abs(len(answer) - len(expected)) > 1:
        return False
    if len(answer) == len(expected):
        diffs = [i for i, (a, b) in enumerate(zip(answer, expected, strict=True)) if a != b]
        if len(diffs) == 1:
            return True
        return (
            len(diffs) == 2
            and diffs[1] == diffs[0] + 1
            and answer[diffs[0]] == expected[diffs[1]]
            and answer[diffs[1]] == expected[diffs[0]]
        )
    shorter, longer = sorted((answer, expected), key=len)
    return any(longer[:i] + longer[i + 1 :] == shorter for i in range(len(longer)))


def check_spanish(answer: str, expected_form: str, lemma: str) -> SpanishCheck:
    given, expected = normalize(answer), normalize(expected_form)
    if not given:
        return SpanishCheck.WRONG
    if given == expected:
        return SpanishCheck.EXACT
    if strip_accents(given) == strip_accents(expected):
        return SpanishCheck.ACCENT_SLIP
    if len(expected) >= MIN_LENGTH_FOR_TYPO and _within_one_edit(
        strip_accents(given), strip_accents(expected)
    ):
        return SpanishCheck.TYPO
    if strip_accents(given) == strip_accents(normalize(lemma)):
        return SpanishCheck.OTHER_FORM
    return SpanishCheck.WRONG


async def judge_translation(
    llm: LLMClient, answer: str, word: str, sentence: str
) -> TranslationVerdict:
    if not normalize(answer):
        return TranslationVerdict(verdict="wrong", reason="Відповіді немає.", expected="")
    return await llm(
        TranslationVerdict,
        system=JUDGE_SYSTEM,
        prompt=f"Word: {word}\nSentence: {sentence}\nLearner's answer: {answer.strip()}",
        effort="low",
        max_tokens=4_000,
    )
