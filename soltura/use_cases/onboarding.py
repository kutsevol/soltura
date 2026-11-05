import logging
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from soltura.language.frequency import BANDS
from soltura.learner.repository import sample_lexemes
from soltura.llm.client import LLMClient
from soltura.onboarding.service import (
    CONTENT_POS,
    SAMPLED_PER_BAND,
    SENTENCES_SYSTEM,
    WORDS_PER_BAND,
    Finished,
    LearnOutcome,
    MissedSummary,
    NextWord,
    NothingToAnswer,
    PlacementItem,
    PlacementResult,
    PlacementSentences,
    apply_placement,
    band_scores,
    get_latest_placement,
    judge_items,
    learn_missed_words,
    missed_summary,
    score_placement,
    should_stop,
)
from soltura.practice.text import split_around
from soltura.reading.service import vocabulary_range
from soltura.words.vocabulary import VocabularyMap, build_vocabulary_map

logger = logging.getLogger(__name__)


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


async def learn_from_result(session: AsyncSession, learner_id: int, now: datetime) -> LearnOutcome:
    added, _ = await learn_missed_words(session, learner_id, now)
    return LearnOutcome(added=added, missed=await missed_summary(session, learner_id))


@dataclass(frozen=True)
class ResultScreen:
    result: PlacementResult
    vocabulary: VocabularyMap
    reading_range: int
    missed: MissedSummary


async def result_screen(
    session: AsyncSession, learner_id: int, result: PlacementResult
) -> ResultScreen:
    return ResultScreen(
        result=result,
        vocabulary=await build_vocabulary_map(session, learner_id),
        reading_range=await vocabulary_range(session, learner_id),
        missed=await missed_summary(session, learner_id),
    )


async def latest_result_screen(session: AsyncSession, learner_id: int) -> ResultScreen | None:
    result = await get_latest_placement(session, learner_id)
    if result is None:
        return None
    return await result_screen(session, learner_id, result)
