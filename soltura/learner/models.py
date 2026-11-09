from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlmodel import Field, SQLModel

import soltura.db  # noqa: F401  (applies the metadata naming convention before tables are defined)


class CefrLevel(StrEnum):
    A1 = "a1"
    A2 = "a2"
    B1 = "b1"
    B2 = "b2"
    C1 = "c1"
    C2 = "c2"


class LexemeStatus(StrEnum):
    KNOWN = "known"
    LEARNING = "learning"


class LexemeOrigin(StrEnum):
    ONBOARDING = "onboarding"
    READING = "reading"


class KnowledgeType(StrEnum):
    RECOGNIZE = "recognize"
    RECALL = "recall"


class UnitKind(StrEnum):
    WORD = "word"
    CONJUGATION = "conjugation"
    GRAMMAR = "grammar"


class CardState(StrEnum):
    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"


class Rating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


class ReviewSource(StrEnum):
    WARMUP = "warmup"
    READING_TAP = "reading_tap"
    CONJUGATION = "conjugation"
    GRAMMAR = "grammar"
    WRITING = "writing"


class ErrorKind(StrEnum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    SPELLING = "spelling"
    OTHER = "other"


class StudyStep(StrEnum):
    WARMUP = "warmup"
    READING = "reading"
    GRAMMAR = "grammar"
    WRITING = "writing"
    DONE = "done"


def _enum_column(enum: type[StrEnum], name: str, **kwargs: Any) -> Column[Any]:
    return Column(
        Enum(enum, name=name, values_callable=lambda members: [m.value for m in members]),
        nullable=False,
        **kwargs,
    )


def _created_at() -> Any:
    return Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
        description="When the row was created",
    )


def _updated_at() -> Any:
    return Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
        ),
        description="When the row was last changed",
    )


def _lexeme_fk() -> Any:
    return Field(
        sa_column=Column(Integer, ForeignKey("lexeme.id", ondelete="CASCADE"), nullable=False),
        description="Spanish lemma the row is about",
    )


class Learner(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, description="Learner id")
    telegram_user_id: int = Field(
        sa_column=Column(BigInteger, nullable=False, unique=True),
        description="Telegram user id the learner logs in with",
    )
    native_language: str = Field(
        default="uk",
        sa_column=Column(String(8), server_default="uk", nullable=False),
        description="ISO 639-1 code of the language explanations and translations use",
    )
    target_level: CefrLevel = Field(
        default=CefrLevel.B1,
        sa_column=_enum_column(CefrLevel, "cefr_level", server_default=CefrLevel.B1.value),
        description="CEFR level the learner is working towards",
    )
    reading_level: CefrLevel | None = Field(
        default=None,
        sa_column=Column(
            Enum(
                CefrLevel,
                name="cefr_level",
                values_callable=lambda members: [m.value for m in members],
                create_type=False,
            ),
            nullable=True,
        ),
        description="Measured reading level; unset until placement",
    )
    created_at: datetime = _created_at()
    updated_at: datetime = _updated_at()


class Lexeme(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True, description="Lexeme id")
    lemma: str = Field(
        sa_column=Column(String(64), nullable=False, unique=True),
        description="Spanish lemma as spaCy produces it, lowercase",
    )
    pos: str = Field(
        sa_column=Column(String(8), nullable=False),
        description="Most frequent Universal POS tag of the lemma, e.g. NOUN or VERB",
    )
    frequency_rank: int = Field(
        sa_column=Column(Integer, nullable=False, index=True),
        description="1 for the most frequent lemma",
    )


class LearnerLexeme(SQLModel, table=True):
    __tablename__ = "learner_lexeme"

    learner_id: int = Field(
        sa_column=Column(Integer, ForeignKey("learner.id", ondelete="CASCADE"), primary_key=True),
        description="Learner the lemma belongs to",
    )
    lexeme_id: int = Field(
        sa_column=Column(Integer, ForeignKey("lexeme.id", ondelete="CASCADE"), primary_key=True),
        description="Lemma the learner knows or is learning",
    )
    status: LexemeStatus = Field(
        sa_column=_enum_column(LexemeStatus, "lexeme_status"),
        description="Whether the lemma counts as known or is being learned",
    )
    origin: LexemeOrigin = Field(
        sa_column=_enum_column(LexemeOrigin, "lexeme_origin"),
        description="How the lemma entered the learner model",
    )
    created_at: datetime = _created_at()
    updated_at: datetime = _updated_at()


class WordContext(SQLModel, table=True):
    __tablename__ = "word_context"
    __table_args__ = (Index("ix_word_context_learner_id_lexeme_id", "learner_id", "lexeme_id"),)

    id: int | None = Field(default=None, primary_key=True, description="Context id")
    learner_id: int = Field(
        sa_column=Column(Integer, ForeignKey("learner.id", ondelete="CASCADE"), nullable=False),
        description="Learner who saved the word",
    )
    lexeme_id: int = _lexeme_fk()
    sentence: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Spanish sentence the word was saved from",
    )
    topic: str | None = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
        description="Topic of the text the sentence came from",
    )
    created_at: datetime = _created_at()


class MemoryCard(SQLModel, table=True):
    __tablename__ = "memory_card"
    __table_args__ = (
        UniqueConstraint("learner_id", "lexeme_id", "knowledge_type"),
        UniqueConstraint("learner_id", "unit_kind", "unit_key", "knowledge_type"),
        Index("ix_memory_card_learner_id_due", "learner_id", "due"),
    )

    id: int | None = Field(default=None, primary_key=True, description="Card id")
    learner_id: int = Field(
        sa_column=Column(Integer, ForeignKey("learner.id", ondelete="CASCADE"), nullable=False),
        description="Learner the card belongs to",
    )
    unit_kind: UnitKind = Field(
        default=UnitKind.WORD,
        sa_column=_enum_column(UnitKind, "unit_kind", server_default=UnitKind.WORD.value),
        description="What the card schedules: a word, a conjugated form or a grammar item",
    )
    # Nullable until a later release tightens it: the migration backfills existing rows,
    # and code from before it still inserts cards without a key.
    unit_key: str | None = Field(
        default=None,
        sa_column=Column(String(64), nullable=True),
        description="Identifies the unit within its kind; for a word, its lexeme id",
    )
    lexeme_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("lexeme.id", ondelete="CASCADE"), nullable=True),
        description="Spanish lemma of a word card; unset for every other kind of unit",
    )
    knowledge_type: KnowledgeType = Field(
        sa_column=_enum_column(KnowledgeType, "knowledge_type"),
        description="Which kind of knowing this card schedules",
    )
    state: CardState = Field(
        default=CardState.LEARNING,
        sa_column=_enum_column(CardState, "card_state", server_default=CardState.LEARNING.value),
        description="FSRS card state",
    )
    step: int | None = Field(
        default=0,
        sa_column=Column(Integer, nullable=True),
        description="FSRS learning or relearning step; unset in the review state",
    )
    stability: float | None = Field(
        default=None,
        description="FSRS stability in days; unset before the first review",
    )
    difficulty: float | None = Field(
        default=None,
        description="FSRS difficulty; unset before the first review",
    )
    due: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        description="When the card is next due",
    )
    last_review: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
        description="When the card was last reviewed",
    )
    created_at: datetime = _created_at()
    updated_at: datetime = _updated_at()


class PlacementRun(SQLModel, table=True):
    __tablename__ = "placement_run"

    id: int | None = Field(default=None, primary_key=True, description="Placement run id")
    learner_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("learner.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        description="Learner who took the placement test",
    )
    known_rank: int = Field(
        sa_column=Column(Integer, nullable=False),
        description="Frequency rank up to which words were marked known; 0 when no band passed",
    )
    bands: list[dict[str, int]] = Field(
        sa_column=Column(JSON, nullable=False),
        description="Score per frequency band: band, max_rank, correct and total",
    )
    items: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSON, nullable=True),
        description="Every word asked with the answer, verdict and expected meaning; unset for runs saved before answers were kept",
    )
    created_at: datetime = _created_at()


class ReadingText(SQLModel, table=True):
    __tablename__ = "reading_text"

    id: int | None = Field(default=None, primary_key=True, description="Reading text id")
    learner_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("learner.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        description="Learner the text was prepared for",
    )
    topic: str | None = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
        description="Topic the learner asked for; unset when they pasted a text",
    )
    title: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Title of the prepared text",
    )
    created_at: datetime = _created_at()


class JournalEntry(SQLModel, table=True):
    __tablename__ = "journal_entry"

    id: int | None = Field(default=None, primary_key=True, description="Journal entry id")
    learner_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("learner.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        description="Learner who wrote the text",
    )
    prompt: str | None = Field(
        default=None,
        sa_column=Column(String(200), nullable=True),
        description="The task or topic the text answers; unset for a free topic",
    )
    body: str = Field(
        sa_column=Column(Text, nullable=False),
        description="The text as the learner wrote it",
    )
    corrected: str = Field(
        sa_column=Column(Text, nullable=False),
        description="The text after the correction",
    )
    created_at: datetime = _created_at()


class ErrorLog(SQLModel, table=True):
    __tablename__ = "error_log"

    id: int | None = Field(default=None, primary_key=True, description="Error id")
    entry_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("journal_entry.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        description="Journal entry the error was found in",
    )
    learner_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("learner.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        description="Learner who made the error",
    )
    kind: ErrorKind = Field(
        sa_column=_enum_column(ErrorKind, "error_kind"),
        description="Whether the error is a grammar rule, a word, spelling or something else",
    )
    unit_id: str | None = Field(
        default=None,
        sa_column=Column(String(64), nullable=True),
        description="Id of the grammar unit the error belongs to; set only for a grammar error",
    )
    original: str = Field(
        sa_column=Column(Text, nullable=False),
        description="The fragment as the learner wrote it",
    )
    corrected: str = Field(
        sa_column=Column(Text, nullable=False),
        description="The fragment after the correction",
    )
    note: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Why the fragment is wrong, in the learner's language",
    )
    created_at: datetime = _created_at()


class StudySession(SQLModel, table=True):
    __tablename__ = "study_session"

    id: int | None = Field(default=None, primary_key=True, description="Study session id")
    learner_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("learner.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        description="Learner who is studying",
    )
    topic: str = Field(
        sa_column=Column(String(100), nullable=False),
        description="Label of the reading topic the whole session is about",
    )
    step: StudyStep = Field(
        default=StudyStep.WARMUP,
        sa_column=_enum_column(StudyStep, "study_step", server_default=StudyStep.WARMUP.value),
        description="The step the learner is on; done once the session is over",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False),
        description="Moment the learner started the session",
    )
    finished_at: datetime | None = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), nullable=True),
        description="Moment the session ended; unset while it is open",
    )


class ReviewLog(SQLModel, table=True):
    __tablename__ = "review_log"

    id: int | None = Field(default=None, primary_key=True, description="Review id")
    card_id: int = Field(
        sa_column=Column(
            Integer, ForeignKey("memory_card.id", ondelete="CASCADE"), nullable=False, index=True
        ),
        description="Card that was reviewed",
    )
    rating: Rating = Field(
        sa_column=_enum_column(Rating, "rating"),
        description="FSRS rating derived from the checked answer",
    )
    source: ReviewSource = Field(
        sa_column=_enum_column(ReviewSource, "review_source"),
        description="Where the review happened",
    )
    answer: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="What the learner typed; unset for a reading tap",
    )
    duration_ms: int | None = Field(
        default=None,
        description="How long the learner took to answer, in milliseconds",
    )
    reviewed_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), nullable=False),
        description="Moment of the review that FSRS scheduled from",
    )
