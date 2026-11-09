from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, case, func, literal, literal_column
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlmodel import SQLModel, col, select

from soltura.learner.models import (
    ErrorKind,
    ErrorLog,
    JournalEntry,
    KnowledgeType,
    Learner,
    LearnerLexeme,
    Lexeme,
    LexemeOrigin,
    LexemeStatus,
    MemoryCard,
    PlacementRun,
    Rating,
    ReadingText,
    ReviewLog,
    UnitKind,
    WordContext,
)

_LEARNER_LEXEME = SQLModel.metadata.tables["learner_lexeme"]

# spaCy tags ser, estar, poder and deber as auxiliaries; they are verbs to conjugate.
VERB_TAGS = ("VERB", "AUX")


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
    session: AsyncSession, learner_id: int, now: datetime, limit: int, unit_kind: UnitKind
) -> list[MemoryCard]:
    result = await session.execute(
        select(MemoryCard)
        .where(
            col(MemoryCard.learner_id) == learner_id,
            col(MemoryCard.unit_kind) == unit_kind,
            col(MemoryCard.due) <= now,
        )
        .order_by(col(MemoryCard.due), col(MemoryCard.id))
        .limit(limit)
    )
    return list(result.scalars())


async def count_due_cards(
    session: AsyncSession, learner_id: int, now: datetime, unit_kind: UnitKind
) -> int:
    result = await session.execute(
        select(func.count()).where(
            col(MemoryCard.learner_id) == learner_id,
            col(MemoryCard.unit_kind) == unit_kind,
            col(MemoryCard.due) <= now,
        )
    )
    return result.scalar_one()


async def get_unit_keys(session: AsyncSession, learner_id: int, unit_kind: UnitKind) -> set[str]:
    result = await session.execute(
        select(MemoryCard.unit_key).where(
            col(MemoryCard.learner_id) == learner_id,
            col(MemoryCard.unit_kind) == unit_kind,
            col(MemoryCard.unit_key).is_not(None),
        )
    )
    return set(result.scalars())


@dataclass(frozen=True)
class CardProgress:
    unit_key: str
    stability: float | None
    due: datetime
    answers: int
    right: int


async def get_card_progress(
    session: AsyncSession, learner_id: int, unit_kind: UnitKind
) -> list[CardProgress]:
    stats = (
        select(
            col(ReviewLog.card_id).label("card_id"),
            func.count().label("answers"),
            func.count()
            .filter(col(ReviewLog.rating).in_((Rating.GOOD, Rating.EASY)))
            .label("right"),
        )
        .group_by(col(ReviewLog.card_id))
        .subquery()
    )
    result = await session.execute(
        select(
            MemoryCard,
            func.coalesce(stats.c.answers, 0),
            func.coalesce(stats.c.right, 0),
        )
        .outerjoin(stats, stats.c.card_id == col(MemoryCard.id))
        .where(
            col(MemoryCard.learner_id) == learner_id,
            col(MemoryCard.unit_kind) == unit_kind,
            col(MemoryCard.unit_key).is_not(None),
        )
        .order_by(col(MemoryCard.id))
    )
    return [
        CardProgress(card.unit_key, card.stability, card.due, answers, right)
        for card, answers, right in result.all()
        if card.unit_key is not None
    ]


async def count_unreviewed_cards(
    session: AsyncSession, learner_id: int, unit_kind: UnitKind
) -> int:
    result = await session.execute(
        select(func.count()).where(
            col(MemoryCard.learner_id) == learner_id,
            col(MemoryCard.unit_kind) == unit_kind,
            col(MemoryCard.last_review).is_(None),
        )
    )
    return result.scalar_one()


async def get_verb_lemmas(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(Lexeme.lemma)
        .where(col(Lexeme.pos).in_(VERB_TAGS))
        .order_by(col(Lexeme.frequency_rank), col(Lexeme.lemma))
    )
    return list(result.scalars())


async def save_placement_run(
    session: AsyncSession,
    learner_id: int,
    known_rank: int,
    bands: list[dict[str, int]],
    items: list[dict[str, Any]] | None = None,
) -> PlacementRun:
    run = PlacementRun(learner_id=learner_id, known_rank=known_rank, bands=bands, items=items)
    session.add(run)
    await session.flush()
    return run


async def get_latest_placement_run(session: AsyncSession, learner_id: int) -> PlacementRun | None:
    result = await session.execute(
        select(PlacementRun)
        .where(col(PlacementRun.learner_id) == learner_id)
        .order_by(col(PlacementRun.id).desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def save_reading_text(
    session: AsyncSession, learner_id: int, topic: str | None, title: str
) -> ReadingText:
    text = ReadingText(learner_id=learner_id, topic=topic, title=title)
    session.add(text)
    await session.flush()
    return text


@dataclass(frozen=True)
class JournalError:
    kind: ErrorKind
    unit_id: str | None
    original: str
    corrected: str
    note: str


async def save_journal_entry(
    session: AsyncSession,
    learner_id: int,
    prompt: str | None,
    body: str,
    corrected: str,
    errors: Sequence[JournalError],
) -> JournalEntry:
    entry = JournalEntry(learner_id=learner_id, prompt=prompt, body=body, corrected=corrected)
    session.add(entry)
    await session.flush()
    assert entry.id is not None
    session.add_all(
        ErrorLog(
            entry_id=entry.id,
            learner_id=learner_id,
            kind=error.kind,
            unit_id=error.unit_id,
            original=error.original,
            corrected=error.corrected,
            note=error.note,
        )
        for error in errors
    )
    await session.flush()
    return entry


async def get_journal_entries(
    session: AsyncSession, learner_id: int, limit: int
) -> list[JournalEntry]:
    result = await session.execute(
        select(JournalEntry)
        .where(col(JournalEntry.learner_id) == learner_id)
        .order_by(col(JournalEntry.id).desc())
        .limit(limit)
    )
    return list(result.scalars())


async def get_errors_for_entries(
    session: AsyncSession, entry_ids: Iterable[int]
) -> dict[int, list[ErrorLog]]:
    result = await session.execute(
        select(ErrorLog)
        .where(col(ErrorLog.entry_id).in_(list(entry_ids)))
        .order_by(col(ErrorLog.id))
    )
    errors: dict[int, list[ErrorLog]] = defaultdict(list)
    for error in result.scalars():
        errors[error.entry_id].append(error)
    return errors


# Oldest first: callers take the last error of a group as the latest example.
async def get_learner_errors(session: AsyncSession, learner_id: int) -> list[ErrorLog]:
    result = await session.execute(
        select(ErrorLog).where(col(ErrorLog.learner_id) == learner_id).order_by(col(ErrorLog.id))
    )
    return list(result.scalars())


async def get_recent_titles(session: AsyncSession, learner_id: int, limit: int) -> list[str]:
    result = await session.execute(
        select(ReadingText.title)
        .where(col(ReadingText.learner_id) == learner_id)
        .order_by(col(ReadingText.id).desc())
        .limit(limit)
    )
    return list(result.scalars())


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


async def get_due_recall_cards(
    session: AsyncSession, learner_id: int, lexeme_ids: Iterable[int], now: datetime
) -> list[MemoryCard]:
    result = await session.execute(
        select(MemoryCard).where(
            col(MemoryCard.learner_id) == learner_id,
            col(MemoryCard.lexeme_id).in_(set(lexeme_ids)),
            col(MemoryCard.knowledge_type) == KnowledgeType.RECALL,
            col(MemoryCard.due) <= now,
        )
    )
    return list(result.scalars())


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


async def mark_lemmas_known(session: AsyncSession, learner_id: int, lemmas: Iterable[str]) -> None:
    # Like marking by rank, it leaves words already in the learner model as they are, and
    # it does not commit: the caller's transaction decides.
    rows = select(
        literal(learner_id),
        col(Lexeme.id),
        literal(LexemeStatus.KNOWN, type_=_LEARNER_LEXEME.c.status.type),
        literal(LexemeOrigin.ONBOARDING, type_=_LEARNER_LEXEME.c.origin.type),
    ).where(col(Lexeme.lemma).in_(set(lemmas)))
    await session.execute(
        insert(LearnerLexeme)
        .from_select(["learner_id", "lexeme_id", "status", "origin"], rows)
        .on_conflict_do_nothing(index_elements=["learner_id", "lexeme_id"])
    )


@dataclass(frozen=True)
class BandCounts:
    total: int
    known: int
    learning: int


async def get_vocabulary_bands(
    session: AsyncSession, learner_id: int, edges: Sequence[tuple[int, int]]
) -> list[BandCounts]:
    # Names say nothing about vocabulary, and a rank outside every band (a word the
    # frequency seed never saw) belongs to none. The band index is a literal because a
    # bound parameter in SELECT and again in GROUP BY would be two different values to
    # Postgres.
    band = case(
        *(
            (col(Lexeme.frequency_rank).between(low, high), literal_column(str(index)))
            for index, (low, high) in enumerate(edges)
        )
    ).label("band")
    result = await session.execute(
        select(
            band,
            func.count(),
            func.count().filter(col(LearnerLexeme.status) == LexemeStatus.KNOWN),
            func.count().filter(col(LearnerLexeme.status) == LexemeStatus.LEARNING),
        )
        .select_from(Lexeme)
        .outerjoin(
            LearnerLexeme,
            and_(
                col(LearnerLexeme.lexeme_id) == col(Lexeme.id),
                col(LearnerLexeme.learner_id) == learner_id,
            ),
        )
        .where(
            col(Lexeme.pos) != "PROPN",
            col(Lexeme.frequency_rank).between(edges[0][0], edges[-1][1]),
        )
        .group_by(band)
    )
    counts = {index: BandCounts(total, known, learning) for index, total, known, learning in result}
    return [counts.get(index, BandCounts(0, 0, 0)) for index in range(len(edges))]


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
