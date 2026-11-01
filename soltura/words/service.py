import asyncio
import logging
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.nlp import analyze
from soltura.learner.models import LexemeStatus
from soltura.learner.repository import get_learner_lemmas
from soltura.llm.client import LLMClient, LLMNotConfiguredError, LLMUnavailableError
from soltura.practice.text import split_around

logger = logging.getLogger(__name__)

ATTEMPTS = 2
MAX_WORDS = 20

ENTRY_SYSTEM = (
    "You are a Spanish dictionary for an adult Ukrainian speaker who lives in Spain and is at "
    "CEFR level A2. You get one word as the learner typed it, in any form and possibly with a "
    "typo. Give its dictionary form (lemma, lowercase), its meaning in Ukrainian in a few words, "
    "and one short natural sentence from everyday life in Spain, at level A2, that uses the "
    "word in any form that fits. If the input is not a Spanish word even allowing for typos, "
    "say so."
)


class WordEntry(BaseModel):
    is_spanish_word: bool = Field(
        description="False when the input is not a Spanish word, even allowing for a typo"
    )
    lemma: str = Field(description="Dictionary form of the word, lowercase")
    translation: str = Field(description="Meaning of the word in Ukrainian, in a few words")
    sentence: str = Field(description="One short Spanish sentence that uses the word")


class NotASpanishWordError(Exception):
    pass


class WordLookupFailedError(Exception):
    pass


class Problem(StrEnum):
    MULTIPLE_WORDS = "multiple_words"
    NOT_SPANISH = "not_spanish"
    NO_EXAMPLE = "no_example"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class WordLookup:
    lemma: str
    translation: str
    sentence: str
    saved: bool


@dataclass(frozen=True)
class LineResult:
    word: str
    lookup: WordLookup | None = None
    problem: Problem | None = None


def parse_words(text: str) -> list[str]:
    # One word per line; blank lines and repeats (ignoring case) are dropped, order kept.
    return list(
        dict.fromkeys(line.strip().casefold() for line in text.splitlines() if line.strip())
    )


def _uses_word(sentence: str, typed: str, lemma: str) -> bool:
    # The model may inflect the word, so a spaCy lemma match counts as well as the
    # typed form or the lemma itself standing in the sentence.
    return (
        split_around(sentence, typed) is not None
        or split_around(sentence, lemma) is not None
        or any(token.lemma == lemma for token in analyze(sentence))
    )


async def _ask(llm: LLMClient, word: str) -> WordEntry:
    for attempt in range(1, ATTEMPTS + 1):
        entry = await llm(
            WordEntry,
            system=ENTRY_SYSTEM,
            prompt=f"Word: {word}",
            effort="low",
            max_tokens=4_000,
        )
        if not entry.is_spanish_word:
            raise NotASpanishWordError(word)
        lemma = entry.lemma.strip().lower()
        if lemma and _uses_word(entry.sentence, word, lemma):
            return entry.model_copy(
                update={
                    "lemma": lemma,
                    "translation": entry.translation.strip(),
                    "sentence": entry.sentence.strip(),
                }
            )
        logger.debug(f"Discarded entry for {word!r} (attempt {attempt}): {entry.sentence!r}")
    raise WordLookupFailedError(word)


async def _ask_line(llm: LLMClient, word: str) -> WordEntry | Problem:
    if len(word.split()) > 1:
        return Problem.MULTIPLE_WORDS
    try:
        return await _ask(llm, word)
    except NotASpanishWordError:
        return Problem.NOT_SPANISH
    except WordLookupFailedError:
        return Problem.NO_EXAMPLE
    except LLMNotConfiguredError:
        raise
    except LLMUnavailableError as error:
        logger.warning(f"Lookup of {word!r} failed: {error}")
        return Problem.UNAVAILABLE


async def look_up_words(
    session: AsyncSession, llm: LLMClient, learner_id: int, words: list[str]
) -> list[LineResult]:
    # Only the model calls run concurrently: one AsyncSession cannot serve two queries
    # at once, so the saved-word check is a single query after they finish.
    outcomes = await asyncio.gather(*(_ask_line(llm, word) for word in words))
    saved = await get_learner_lemmas(session, learner_id, {LexemeStatus.LEARNING})
    results: list[LineResult] = []
    seen: set[str] = set()
    for word, outcome in zip(words, outcomes, strict=True):
        if isinstance(outcome, Problem):
            results.append(LineResult(word=word, problem=outcome))
        elif outcome.lemma not in seen:
            # "nieto" and "nietos" are one word: the first line keeps it.
            seen.add(outcome.lemma)
            lookup = WordLookup(
                lemma=outcome.lemma,
                translation=outcome.translation,
                sentence=outcome.sentence,
                saved=outcome.lemma in saved,
            )
            results.append(LineResult(word=word, lookup=lookup))
    return results
