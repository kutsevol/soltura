import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from wordfreq import top_n_list, word_frequency

from soltura.db import get_engine, get_session_factory
from soltura.language.nlp import analyze_words
from soltura.learner.models import Lexeme

logger = logging.getLogger(__name__)

SEED_SIZE = 10_000
MAX_LEMMA_LENGTH = 64


@dataclass(frozen=True)
class RankedLemma:
    lemma: str
    pos: str
    frequency_rank: int


def rank_lemmas(word_frequencies: dict[str, float]) -> list[RankedLemma]:
    # Each word form is lemmatized on its own, the same way a text's forms are, and
    # its frequency is added to the lemma it maps to: "es", "son" and "fue" all feed "ser".
    words = list(word_frequencies)
    lemma_frequency: defaultdict[str, float] = defaultdict(float)
    pos_frequency: defaultdict[str, defaultdict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for word, tokens in zip(words, analyze_words(words), strict=True):
        if len(tokens) != 1 or len(tokens[0].lemma) > MAX_LEMMA_LENGTH:
            continue
        token = tokens[0]
        lemma_frequency[token.lemma] += word_frequencies[word]
        pos_frequency[token.lemma][token.pos] += word_frequencies[word]

    by_frequency = sorted(lemma_frequency, key=lambda lemma: -lemma_frequency[lemma])
    return [
        RankedLemma(lemma=lemma, pos=_main_pos(pos_frequency[lemma]), frequency_rank=rank)
        for rank, lemma in enumerate(by_frequency, start=1)
    ]


def _main_pos(pos_frequency: dict[str, float]) -> str:
    # PROPN only when no form of the lemma was tagged anything else: "casa" is PROPN
    # alone but NOUN as "casas", while "madrid" stays a name.
    common = {pos: total for pos, total in pos_frequency.items() if pos != "PROPN"}
    candidates = common or pos_frequency
    return max(candidates, key=lambda pos: candidates[pos])


async def save_lexemes(session: AsyncSession, ranked: list[RankedLemma]) -> None:
    rows = [
        {"lemma": item.lemma, "pos": item.pos, "frequency_rank": item.frequency_rank}
        for item in ranked
    ]
    statement = insert(Lexeme)
    # Re-seeding refreshes ranks and tags in place, so ids stay stable for the
    # learner tables that point at them.
    upsert = statement.on_conflict_do_update(
        index_elements=["lemma"],
        set_={"pos": statement.excluded.pos, "frequency_rank": statement.excluded.frequency_rank},
    )
    for start in range(0, len(rows), 1000):
        await session.execute(upsert, rows[start : start + 1000])
    await session.commit()


def spanish_word_frequencies(size: int = SEED_SIZE) -> dict[str, float]:
    return {word: word_frequency(word, "es") for word in top_n_list("es", size)}


async def main() -> None:
    ranked = rank_lemmas(spanish_word_frequencies())
    async with get_session_factory()() as session:
        await save_lexemes(session, ranked)
    await get_engine().dispose()
    logger.info(f"Seeded {len(ranked)} lexemes")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
