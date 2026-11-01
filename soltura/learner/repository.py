from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import and_, func, literal
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlmodel import SQLModel, col, select

from soltura.learner.models import (
    KnowledgeType,
    Learner,
    LearnerLexeme,
    Lexeme,
    LexemeOrigin,
    LexemeStatus,
    MemoryCard,
    WordContext,
)

_LEARNER_LEXEME = SQLModel.metadata.tables["learner_lexeme"]


@dataclass(frozen=True)
class SavedWord:
    lemma: str
    status: LexemeStatus
    recognize_due: datetime
    recall_due: datetime
    sentences: list[str]


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


async def count_due_cards(session: AsyncSession, learner_id: int, now: datetime) -> int:
    result = await session.execute(
        select(func.count()).where(
            col(MemoryCard.learner_id) == learner_id, col(MemoryCard.due) <= now
        )
    )
    return result.scalar_one()


async def count_learning_words(session: AsyncSession, learner_id: int) -> int:
    result = await session.execute(
        select(func.count()).where(
            col(LearnerLexeme.learner_id) == learner_id,
            col(LearnerLexeme.status) == LexemeStatus.LEARNING,
        )
    )
    return result.scalar_one()


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


async def sample_lexemes(
    session: AsyncSession, min_rank: int, max_rank: int, pos: Iterable[str], limit: int
) -> list[Lexeme]:
    result = await session.execute(
        select(Lexeme)
        .where(
            col(Lexeme.frequency_rank).between(min_rank, max_rank),
            col(Lexeme.pos).in_(set(pos)),
        )
        .order_by(func.random())
        .limit(limit)
    )
    return list(result.scalars())


async def mark_known_up_to_rank(session: AsyncSession, learner_id: int, max_rank: int) -> None:
    # Words already being learned keep their status: the tap that saved them is
    # better evidence than a placement estimate. The literals carry the enum column
    # types, or Postgres would refuse varchar values for an enum column.
    rows = select(
        literal(learner_id),
        col(Lexeme.id),
        literal(LexemeStatus.KNOWN, type_=_LEARNER_LEXEME.c.status.type),
        literal(LexemeOrigin.ONBOARDING, type_=_LEARNER_LEXEME.c.origin.type),
    ).where(col(Lexeme.frequency_rank) <= max_rank)
    await session.execute(
        insert(LearnerLexeme)
        .from_select(["learner_id", "lexeme_id", "status", "origin"], rows)
        .on_conflict_do_nothing(index_elements=["learner_id", "lexeme_id"])
    )
    await session.commit()


async def get_saved_words(
    session: AsyncSession, learner_id: int, search: str = ""
) -> list[SavedWord]:
    # A saved word is one with both cards; placement-seeded known words have none.
    recognize = aliased(MemoryCard)
    recall = aliased(MemoryCard)
    query = (
        select(Lexeme, LearnerLexeme.status, recognize.due, recall.due)
        .join(LearnerLexeme, col(LearnerLexeme.lexeme_id) == col(Lexeme.id))
        .join(
            recognize,
            and_(
                col(recognize.lexeme_id) == col(Lexeme.id),
                col(recognize.learner_id) == learner_id,
                col(recognize.knowledge_type) == KnowledgeType.RECOGNIZE,
            ),
        )
        .join(
            recall,
            and_(
                col(recall.lexeme_id) == col(Lexeme.id),
                col(recall.learner_id) == learner_id,
                col(recall.knowledge_type) == KnowledgeType.RECALL,
            ),
        )
        .where(col(LearnerLexeme.learner_id) == learner_id)
        .order_by(func.least(recognize.due, recall.due), col(Lexeme.lemma))
    )
    if search:
        query = query.where(col(Lexeme.lemma).icontains(search, autoescape=True))
    rows = [
        (lexeme.id, lexeme.lemma, LexemeStatus(status), recognize_due, recall_due)
        for lexeme, status, recognize_due, recall_due in (await session.execute(query)).all()
        if lexeme.id is not None
    ]
    contexts = await session.execute(
        select(WordContext.lexeme_id, WordContext.sentence)
        .where(
            col(WordContext.learner_id) == learner_id,
            col(WordContext.lexeme_id).in_({lexeme_id for lexeme_id, *_ in rows}),
        )
        .order_by(col(WordContext.created_at).desc(), col(WordContext.id).desc())
    )
    sentences: defaultdict[int, list[str]] = defaultdict(list)
    for lexeme_id, sentence in contexts:
        sentences[lexeme_id].append(sentence)
    return [
        SavedWord(lemma, status, recognize_due, recall_due, sentences[lexeme_id])
        for lexeme_id, lemma, status, recognize_due, recall_due in rows
    ]
