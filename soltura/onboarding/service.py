import asyncio
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import LexemeStatus
from soltura.learner.repository import (
    get_latest_placement_run,
    get_learner_lemmas,
    get_lexemes_by_lemmas,
    mark_known_up_to_rank,
    mark_lemmas_known,
    sample_lexemes,
    save_placement_run,
)
from soltura.llm.client import LLMClient
from soltura.practice.checking import KNOWN_WORD_JUDGE_SYSTEM, judge_translation
from soltura.practice.text import split_around
from soltura.srs.service import save_word

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
WORDS_PER_BAND = 8
# A few spare words per band take the place of names and of words without a usable sentence.
SAMPLED_PER_BAND = WORDS_PER_BAND + 2
PASS_SHARE = 0.6
# Two bands in a row at or under this share end the test: the words only get rarer.
WEAK_SHARE = 0.5
WEAK_BANDS_IN_A_ROW = 2
# Function words are known long before their rank says anything; content words are
# what a vocabulary estimate rests on.
CONTENT_POS = ("NOUN", "VERB", "ADJ", "ADV")
JUDGE_CONCURRENCY = 8
# Words the learner did not know that one press adds to learning; more would flood the warm-up.
LEARN_BATCH = 15

SENTENCES_SYSTEM = (
    "You write short, natural Spanish sentences from everyday life in Spain for a vocabulary "
    "placement test. For each word, write one sentence of at most 12 words that uses it in "
    "its most common meaning, in any form that fits, with words simpler than the target "
    "around it. Give the word exactly as it appears in your sentence, and its meaning in "
    "that sentence in Ukrainian, in a few words. Mark a word as unusable when it is not a "
    "standard dictionary word: the name of a person or a place, a typo, a verb form with "
    "a pronoun attached or anything else a dictionary would not list."
)


class PlacementSentence(BaseModel):
    lemma: str = Field(description="The word as it was given")
    sentence: str = Field(description="The Spanish sentence using it")
    target_form: str = Field(description="The word exactly as it appears in the sentence")
    meaning: str = Field(description="The word's meaning in this sentence, in Ukrainian")
    is_usable: bool = Field(
        default=True,
        description="False when the word is a name, a typo or otherwise not a dictionary word",
    )


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
    verdict: str = Field(default="", description="The judge's verdict; empty until judged")
    reason: str = Field(default="", description="The judge's one-line reason in Ukrainian")
    expected: str = Field(default="", description="The word's meaning in this sentence")


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
        lexemes = await sample_lexemes(session, min_rank, max_rank, CONTENT_POS, SAMPLED_PER_BAND)
        sampled.extend((band, lexeme.lemma) for lexeme in lexemes)
    if not sampled:
        return []

    # One call for every sentence: separate calls would cost more and keep the learner
    # waiting for the slowest of them.
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
        if not sentence.is_usable:
            logger.debug(f"Placement word {lemma!r} is not a dictionary word")
            continue
        if sentence.target_form.lower() in {item.target_form.lower() for item in items}:
            logger.debug(f"Placement word {sentence.target_form!r} is already asked")
            continue
        if sum(item.band == band for item in items) == WORDS_PER_BAND:
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


async def judge_items(llm: LLMClient, items: list[PlacementItem]) -> list[PlacementItem]:
    limit = asyncio.Semaphore(JUDGE_CONCURRENCY)

    async def judge(item: PlacementItem) -> PlacementItem:
        if item.verdict:
            return item
        async with limit:
            verdict = await judge_translation(
                llm, item.answer, item.target_form, item.sentence, KNOWN_WORD_JUDGE_SYSTEM
            )
        # A skipped word is never sent to the judge, so its meaning is the one written with
        # the sentence.
        return item.model_copy(
            update={
                "verdict": verdict.verdict,
                "reason": verdict.reason,
                "expected": verdict.expected or item.meaning,
            }
        )

    return list(await asyncio.gather(*(judge(item) for item in items)))


def band_scores(judged: list[PlacementItem]) -> list[BandScore]:
    scores: list[BandScore] = []
    for band, (_, max_rank) in enumerate(BANDS):
        marks = [item.verdict == "correct" for item in judged if item.band == band]
        if marks:
            scores.append(
                BandScore(band=band, max_rank=max_rank, correct=sum(marks), total=len(marks))
            )
    return scores


def should_stop(scores: list[BandScore]) -> bool:
    last = scores[-WEAK_BANDS_IN_A_ROW:]
    return len(last) == WEAK_BANDS_IN_A_ROW and all(
        score.correct / score.total <= WEAK_SHARE for score in last
    )


async def score_placement(llm: LLMClient, answered: list[PlacementItem]) -> PlacementResult:
    judged = await judge_items(llm, answered)
    words = [
        WordResult(
            band=item.band,
            lemma=item.lemma,
            sentence=item.sentence,
            target_form=item.target_form,
            answer=item.answer,
            verdict=item.verdict,
            reason=item.reason,
            expected=item.expected,
        )
        for item in judged
    ]
    scores = band_scores(judged)

    # Bands count only in an unbroken run from the most frequent one: knowing a few
    # rare words does not mean knowing every more frequent one in between.
    known_rank = 0
    for score in scores:
        if score.correct / score.total < PASS_SHARE:
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
    # A word answered right is known wherever its band is: it was shown and translated.
    await mark_lemmas_known(
        session, learner_id, [word.lemma for word in result.words if word.verdict == "correct"]
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


async def missed_words(session: AsyncSession, learner_id: int) -> list[WordResult]:
    # The words of the latest run that were not answered right and are not being learned
    # yet, most frequent first.
    result = await get_latest_placement(session, learner_id)
    if result is None:
        return []
    learning = await get_learner_lemmas(session, learner_id, [LexemeStatus.LEARNING])
    missed = [
        word for word in result.words if word.verdict != "correct" and word.lemma not in learning
    ]
    ranks = {
        lexeme.lemma: lexeme.frequency_rank
        for lexeme in await get_lexemes_by_lemmas(session, [word.lemma for word in missed])
    }
    return sorted((word for word in missed if word.lemma in ranks), key=lambda w: ranks[w.lemma])


async def learn_missed_words(
    session: AsyncSession, learner_id: int, now: datetime
) -> tuple[int, int]:
    missed = await missed_words(session, learner_id)
    batch = missed[:LEARN_BATCH]
    lexemes = {
        lexeme.lemma: lexeme
        for lexeme in await get_lexemes_by_lemmas(session, [word.lemma for word in batch])
    }
    for word in batch:
        lexeme_id = lexemes[word.lemma].id
        if lexeme_id is None:
            raise ValueError(f"Lexeme for {word.lemma!r} has no id")
        await save_word(session, learner_id, lexeme_id, word.sentence, now)
    return len(batch), len(missed) - len(batch)


class NothingToAnswer(Exception):
    pass


@dataclass(frozen=True)
class NextWord:
    queue: list[PlacementItem]
    answered: list[PlacementItem]


@dataclass(frozen=True)
class Finished:
    result: PlacementResult


async def answer_word(
    session: AsyncSession,
    llm: LLMClient,
    learner_id: int,
    queue: list[PlacementItem],
    answered: list[PlacementItem],
    answer: str,
    give_up: bool,
) -> NextWord | Finished:
    if not queue:
        raise NothingToAnswer
    current, *rest = queue
    done = [*answered, current.model_copy(update={"answer": "" if give_up else answer.strip()})]
    if not rest or rest[0].band != current.band:
        # A band is finished: judge it now, so a learner who has run out of known words
        # is not asked the rarer bands.
        done = await judge_items(llm, done)
        if rest and should_stop(band_scores(done)):
            rest = []
    if rest:
        return NextWord(queue=rest, answered=done)
    result = await score_placement(llm, done)
    await apply_placement(session, learner_id, result)
    return Finished(result)


@dataclass(frozen=True)
class MissedSummary:
    total: int
    batch: int


@dataclass(frozen=True)
class LearnOutcome:
    added: int
    missed: MissedSummary


async def missed_summary(session: AsyncSession, learner_id: int) -> MissedSummary:
    missed = await missed_words(session, learner_id)
    return MissedSummary(total=len(missed), batch=min(len(missed), LEARN_BATCH))


async def learn_from_result(session: AsyncSession, learner_id: int, now: datetime) -> LearnOutcome:
    added, _ = await learn_missed_words(session, learner_id, now)
    return LearnOutcome(added=added, missed=await missed_summary(session, learner_id))
