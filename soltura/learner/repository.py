from collections.abc import Iterable
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.learner.models import (
    KnowledgeType,
    Learner,
    LearnerLexeme,
    Lexeme,
    LexemeStatus,
    MemoryCard,
)


async def get_or_create_learner(session: AsyncSession, telegram_user_id: int) -> Learner:
    # ON CONFLICT DO NOTHING keeps two first requests from the same user from racing
    # into a unique-violation; the select then returns whichever row won.
    await session.execute(
        insert(Learner)
        .values(telegram_user_id=telegram_user_id)
        .on_conflict_do_nothing(index_elements=["telegram_user_id"])
    )
    result = await session.execute(
        select(Learner).where(col(Learner.telegram_user_id) == telegram_user_id)
    )
    learner = result.scalar_one()
    await session.commit()
    return learner


async def get_lexemes_by_lemmas(session: AsyncSession, lemmas: Iterable[str]) -> list[Lexeme]:
    result = await session.execute(select(Lexeme).where(col(Lexeme.lemma).in_(set(lemmas))))
    return list(result.scalars())


async def get_learner_lexemes(
    session: AsyncSession, learner_id: int, lexeme_ids: Iterable[int]
) -> list[LearnerLexeme]:
    result = await session.execute(
        select(LearnerLexeme).where(
            col(LearnerLexeme.learner_id) == learner_id,
            col(LearnerLexeme.lexeme_id).in_(set(lexeme_ids)),
        )
    )
    return list(result.scalars())


async def get_due_cards(
    session: AsyncSession, learner_id: int, now: datetime, limit: int
) -> list[MemoryCard]:
    result = await session.execute(
        select(MemoryCard)
        .where(col(MemoryCard.learner_id) == learner_id, col(MemoryCard.due) <= now)
        .order_by(col(MemoryCard.due), col(MemoryCard.id))
        .limit(limit)
    )
    return list(result.scalars())


async def get_lexemes_by_ids(session: AsyncSession, lexeme_ids: Iterable[int]) -> list[Lexeme]:
    result = await session.execute(select(Lexeme).where(col(Lexeme.id).in_(set(lexeme_ids))))
    return list(result.scalars())


async def get_learner_lemmas(
    session: AsyncSession, learner_id: int, statuses: Iterable[LexemeStatus]
) -> set[str]:
    result = await session.execute(
        select(Lexeme.lemma)
        .join(LearnerLexeme, col(LearnerLexeme.lexeme_id) == col(Lexeme.id))
        .where(
            col(LearnerLexeme.learner_id) == learner_id,
            col(LearnerLexeme.status).in_(set(statuses)),
        )
    )
    return set(result.scalars())


async def get_most_frequent_lemmas(session: AsyncSession, max_rank: int) -> set[str]:
    result = await session.execute(
        select(Lexeme.lemma).where(col(Lexeme.frequency_rank) <= max_rank)
    )
    return set(result.scalars())


async def get_due_card(
    session: AsyncSession,
    learner_id: int,
    lexeme_id: int,
    knowledge_type: KnowledgeType,
    now: datetime,
) -> MemoryCard | None:
    result = await session.execute(
        select(MemoryCard).where(
            col(MemoryCard.learner_id) == learner_id,
            col(MemoryCard.lexeme_id) == lexeme_id,
            col(MemoryCard.knowledge_type) == knowledge_type,
            col(MemoryCard.due) <= now,
        )
    )
    return result.scalar_one_or_none()
