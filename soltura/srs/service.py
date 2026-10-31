from datetime import datetime
from functools import cache

import fsrs
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.config import settings
from soltura.learner.models import (
    CardState,
    KnowledgeType,
    LearnerLexeme,
    LexemeOrigin,
    LexemeStatus,
    MemoryCard,
    Rating,
    ReviewLog,
    ReviewSource,
    WordContext,
)
from soltura.learner.repository import get_due_cards

FSRS_STATE = {
    CardState.LEARNING: fsrs.State.Learning,
    CardState.REVIEW: fsrs.State.Review,
    CardState.RELEARNING: fsrs.State.Relearning,
}
CARD_STATE = {fsrs_state: state for state, fsrs_state in FSRS_STATE.items()}

FSRS_RATING = {
    Rating.AGAIN: fsrs.Rating.Again,
    Rating.HARD: fsrs.Rating.Hard,
    Rating.GOOD: fsrs.Rating.Good,
    Rating.EASY: fsrs.Rating.Easy,
}


@cache
def get_scheduler() -> fsrs.Scheduler:
    return fsrs.Scheduler(desired_retention=settings.srs.desired_retention)


def to_fsrs_card(card: MemoryCard) -> fsrs.Card:
    return fsrs.Card(
        card_id=card.id,
        state=FSRS_STATE[card.state],
        step=card.step,
        stability=card.stability,
        difficulty=card.difficulty,
        due=card.due,
        last_review=card.last_review,
    )


def apply_fsrs_card(card: MemoryCard, fsrs_card: fsrs.Card) -> None:
    card.state = CARD_STATE[fsrs_card.state]
    card.step = fsrs_card.step
    card.stability = fsrs_card.stability
    card.difficulty = fsrs_card.difficulty
    card.due = fsrs_card.due
    card.last_review = fsrs_card.last_review


async def save_word(
    session: AsyncSession,
    learner_id: int,
    lexeme_id: int,
    sentence: str,
    now: datetime,
    topic: str | None = None,
) -> list[MemoryCard]:
    # A tapped word is being learned even if onboarding had marked it known: the tap
    # is the evidence that it is not.
    lexeme_upsert = insert(LearnerLexeme).values(
        learner_id=learner_id,
        lexeme_id=lexeme_id,
        status=LexemeStatus.LEARNING,
        origin=LexemeOrigin.READING,
    )
    await session.execute(
        lexeme_upsert.on_conflict_do_update(
            index_elements=["learner_id", "lexeme_id"],
            set_={"status": LexemeStatus.LEARNING},
        )
    )
    session.add(
        WordContext(learner_id=learner_id, lexeme_id=lexeme_id, sentence=sentence, topic=topic)
    )
    # Saving the same word again adds its new sentence but keeps the cards' history.
    await session.execute(
        insert(MemoryCard)
        .values(
            [
                {
                    "learner_id": learner_id,
                    "lexeme_id": lexeme_id,
                    "knowledge_type": knowledge_type,
                    "due": now,
                    # Core inserts skip model defaults; a new FSRS card starts at learning step 0.
                    "step": 0,
                }
                for knowledge_type in KnowledgeType
            ]
        )
        .on_conflict_do_nothing(index_elements=["learner_id", "lexeme_id", "knowledge_type"])
    )
    result = await session.execute(
        select(MemoryCard)
        .where(col(MemoryCard.learner_id) == learner_id, col(MemoryCard.lexeme_id) == lexeme_id)
        .order_by(col(MemoryCard.knowledge_type))
    )
    cards = list(result.scalars())
    await session.commit()
    return cards


async def review(
    session: AsyncSession,
    card: MemoryCard,
    rating: Rating,
    source: ReviewSource,
    now: datetime,
    answer: str | None = None,
    duration_ms: int | None = None,
    scheduler: fsrs.Scheduler | None = None,
) -> ReviewLog:
    if card.id is None:
        raise ValueError("A card must be saved before it can be reviewed")
    scheduler = scheduler or get_scheduler()
    fsrs_card, _ = scheduler.review_card(to_fsrs_card(card), FSRS_RATING[rating], now)
    apply_fsrs_card(card, fsrs_card)
    log = ReviewLog(
        card_id=card.id,
        rating=rating,
        source=source,
        answer=answer,
        duration_ms=duration_ms,
        reviewed_at=now,
    )
    session.add_all([card, log])
    await session.commit()
    return log


def interleave(cards: list[MemoryCard]) -> list[MemoryCard]:
    # Keeps the oldest-first order but never puts the same word twice in a row, and
    # switches between recognizing and recalling whenever the queue allows it. When
    # only one word's cards are left, they do come back to back.
    remaining = list(cards)
    ordered: list[MemoryCard] = []
    while remaining:
        last = ordered[-1] if ordered else None
        other_words = [
            card for card in remaining if last is None or card.lexeme_id != last.lexeme_id
        ] or remaining
        pick = next(
            (
                card
                for card in other_words
                if last is None or card.knowledge_type != last.knowledge_type
            ),
            other_words[0],
        )
        remaining.remove(pick)
        ordered.append(pick)
    return ordered


async def due_queue(
    session: AsyncSession, learner_id: int, now: datetime, limit: int
) -> list[MemoryCard]:
    return interleave(await get_due_cards(session, learner_id=learner_id, now=now, limit=limit))
