import asyncio
import logging
from dataclasses import asdict, dataclass, field

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.repository import (
    get_latest_placement_run,
    mark_known_up_to_rank,
    sample_lexemes,
    save_placement_run,
)
from soltura.llm.client import LLMClient
from soltura.practice.checking import TranslationVerdict, judge_translation
from soltura.practice.text import split_around

logger = logging.getLogger(__name__)

# Frequency bands from the most frequent lemmas to about B1; a learner who passes all
# of them gets everything up to 6,000 marked known.
BANDS: tuple[tuple[int, int], ...] = (
    (1, 250),
    (251, 500),
    (501, 1000),
    (1001, 1500),
    (1501, 2000),
    (2001, 3000),
    (3001, 4500),
    (4501, 6000),
)
WORDS_PER_BAND = 5
PASS_SHARE = 0.8
# Function words are known long before their rank says anything; content words are
# what a vocabulary estimate rests on.
CONTENT_POS = ("NOUN", "VERB", "ADJ", "ADV")
JUDGE_CONCURRENCY = 8

SENTENCES_SYSTEM = (
    "You write short, natural Spanish sentences from everyday life in Spain for a vocabulary "
    "placement test. For each word, write one sentence of at most 12 words that uses it in "
    "its most common meaning, in any form that fits, with words simpler than the target "
    "around it. Give the word exactly as it appears in your sentence, and its meaning in "
    "that sentence in Ukrainian, in a few words."
)


class PlacementSentence(BaseModel):
    lemma: str = Field(description="The word as it was given")
    sentence: str = Field(description="The Spanish sentence using it")
    target_form: str = Field(description="The word exactly as it appears in the sentence")
    meaning: str = Field(description="The word's meaning in this sentence, in Ukrainian")


class PlacementSentences(BaseModel):
    sentences: list[PlacementSentence] = Field(description="One sentence per given word")


class PlacementItem(BaseModel):
    band: int = Field(description="Index of the frequency band the word comes from")
    lemma: str = Field(description="Dictionary form of the word")
    sentence: str = Field(description="Spanish sentence the word is shown in")
    target_form: str = Field(description="The word exactly as it appears in the sentence")
    meaning: str = Field(
        default="", description="The word's meaning in this sentence, in Ukrainian"
    )
    answer: str = Field(default="", description="The learner's Ukrainian answer")


@dataclass(frozen=True)
class BandScore:
    band: int
    max_rank: int
    correct: int
    total: int


@dataclass(frozen=True)
class WordResult:
    band: int
    lemma: str
    sentence: str
    target_form: str
    answer: str
    verdict: str
    reason: str
    expected: str


@dataclass(frozen=True)
class PlacementResult:
    known_rank: int
    bands: list[BandScore]
    words: list[WordResult] = field(default_factory=list)


async def build_placement(session: AsyncSession, llm: LLMClient) -> list[PlacementItem]:
    sampled: list[tuple[int, str]] = []
    for band, (min_rank, max_rank) in enumerate(BANDS):
        lexemes = await sample_lexemes(session, min_rank, max_rank, CONTENT_POS, WORDS_PER_BAND)
        sampled.extend((band, lexeme.lemma) for lexeme in lexemes)
    if not sampled:
        return []

    # One call for all forty sentences: forty separate calls would cost more and keep
    # the learner waiting for the slowest of them.
    numbered = "\n".join(f"{i}. {lemma}" for i, (_, lemma) in enumerate(sampled, start=1))
    generated = await llm(
        PlacementSentences, system=SENTENCES_SYSTEM, prompt=f"Words:\n{numbered}", effort="low"
    )
    by_lemma = {sentence.lemma.strip().lower(): sentence for sentence in generated.sentences}

    items: list[PlacementItem] = []
    for band, lemma in sampled:
        sentence = by_lemma.get(lemma)
        if sentence is None or split_around(sentence.sentence, sentence.target_form) is None:
            logger.debug(f"No usable placement sentence for {lemma!r}")
            continue
        items.append(
            PlacementItem(
                band=band,
                lemma=lemma,
                sentence=sentence.sentence,
                target_form=sentence.target_form,
                meaning=sentence.meaning,
            )
        )
    return items


async def score_placement(llm: LLMClient, answered: list[PlacementItem]) -> PlacementResult:
    limit = asyncio.Semaphore(JUDGE_CONCURRENCY)

    async def judge(item: PlacementItem) -> TranslationVerdict:
        async with limit:
            return await judge_translation(llm, item.answer, item.target_form, item.sentence)

    verdicts = await asyncio.gather(*(judge(item) for item in answered))
    words = [
        WordResult(
            band=item.band,
            lemma=item.lemma,
            sentence=item.sentence,
            target_form=item.target_form,
            answer=item.answer,
            verdict=verdict.verdict,
            reason=verdict.reason,
            # A skipped word is never sent to the judge, so its meaning is the one written with the sentence.
            expected=verdict.expected or item.meaning,
        )
        for item, verdict in zip(answered, verdicts, strict=True)
    ]

    scores: list[BandScore] = []
    for band, (_, max_rank) in enumerate(BANDS):
        marks = [word.verdict == "correct" for word in words if word.band == band]
        scores.append(BandScore(band=band, max_rank=max_rank, correct=sum(marks), total=len(marks)))

    # Bands count only in an unbroken run from the most frequent one: knowing a few
    # rare words does not mean knowing every more frequent one in between.
    known_rank = 0
    for score in scores:
        if score.total == 0 or score.correct / score.total < PASS_SHARE:
            break
        known_rank = score.max_rank
    return PlacementResult(known_rank=known_rank, bands=scores, words=words)


async def apply_placement(session: AsyncSession, learner_id: int, result: PlacementResult) -> None:
    # The run joins the transaction that marks the words, so a failure keeps neither.
    await save_placement_run(
        session,
        learner_id,
        result.known_rank,
        [asdict(band) for band in result.bands],
        [asdict(word) for word in result.words],
    )
    if result.known_rank > 0:
        await mark_known_up_to_rank(session, learner_id, result.known_rank)
    else:
        await session.commit()


async def get_latest_placement(session: AsyncSession, learner_id: int) -> PlacementResult | None:
    run = await get_latest_placement_run(session, learner_id)
    if run is None:
        return None
    return PlacementResult(
        known_rank=run.known_rank,
        bands=[BandScore(**band) for band in run.bands],
        words=[WordResult(**word) for word in run.items or []],
    )
