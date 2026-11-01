import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.nlp import analyze
from soltura.learner.repository import get_saved_words
from soltura.llm.client import LLMClient
from soltura.practice.text import split_around

logger = logging.getLogger(__name__)

ATTEMPTS = 2

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


@dataclass(frozen=True)
class WordLookup:
    lemma: str
    translation: str
    sentence: str
    saved: bool


def _uses_word(sentence: str, typed: str, lemma: str) -> bool:
    # The model may inflect the word, so a spaCy lemma match counts as well as the
    # typed form or the lemma itself standing in the sentence.
    return (
        split_around(sentence, typed) is not None
        or split_around(sentence, lemma) is not None
        or any(token.lemma == lemma for token in analyze(sentence))
    )


async def look_up_word(
    session: AsyncSession, llm: LLMClient, learner_id: int, word: str
) -> WordLookup:
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
            saved = await get_saved_words(session, learner_id, lemma)
            return WordLookup(
                lemma=lemma,
                translation=entry.translation.strip(),
                sentence=entry.sentence.strip(),
                saved=any(saved_word.lemma == lemma for saved_word in saved),
            )
        logger.debug(f"Discarded entry for {word!r} (attempt {attempt}): {entry.sentence!r}")
    raise WordLookupFailedError(word)
