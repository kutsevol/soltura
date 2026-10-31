from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CEFR_LEVEL = postgresql.ENUM("a1", "a2", "b1", "b2", "c1", "c2", name="cefr_level", create_type=False)
LEXEME_STATUS = postgresql.ENUM("known", "learning", name="lexeme_status", create_type=False)
LEXEME_ORIGIN = postgresql.ENUM("onboarding", "reading", name="lexeme_origin", create_type=False)
KNOWLEDGE_TYPE = postgresql.ENUM("recognize", "recall", name="knowledge_type", create_type=False)
CARD_STATE = postgresql.ENUM(
    "learning", "review", "relearning", name="card_state", create_type=False
)
RATING = postgresql.ENUM("again", "hard", "good", "easy", name="rating", create_type=False)
REVIEW_SOURCE = postgresql.ENUM("warmup", "reading_tap", name="review_source", create_type=False)

ENUMS = (
    CEFR_LEVEL,
    LEXEME_STATUS,
    LEXEME_ORIGIN,
    KNOWLEDGE_TYPE,
    CARD_STATE,
    RATING,
    REVIEW_SOURCE,
)


def _timestamps() -> list[sa.Column[sa.DateTime]]:
    return [
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    for enum in ENUMS:
        enum.create(bind)

    op.create_table(
        "learner",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("native_language", sa.String(8), server_default="uk", nullable=False),
        sa.Column("target_level", CEFR_LEVEL, server_default="b1", nullable=False),
        sa.Column("reading_level", CEFR_LEVEL, nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_learner"),
        sa.UniqueConstraint("telegram_user_id", name="uq_learner_telegram_user_id"),
    )

    op.create_table(
        "lexeme",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lemma", sa.String(64), nullable=False),
        sa.Column("pos", sa.String(8), nullable=False),
        sa.Column("frequency_rank", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_lexeme"),
        sa.UniqueConstraint("lemma", name="uq_lexeme_lemma"),
    )
    op.create_index("ix_lexeme_frequency_rank", "lexeme", ["frequency_rank"])

    op.create_table(
        "learner_lexeme",
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("lexeme_id", sa.Integer(), nullable=False),
        sa.Column("status", LEXEME_STATUS, nullable=False),
        sa.Column("origin", LEXEME_ORIGIN, nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("learner_id", "lexeme_id", name="pk_learner_lexeme"),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_learner_lexeme_learner_id_learner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lexeme_id"],
            ["lexeme.id"],
            name="fk_learner_lexeme_lexeme_id_lexeme",
            ondelete="CASCADE",
        ),
    )

    op.create_table(
        "memory_card",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("lexeme_id", sa.Integer(), nullable=False),
        sa.Column("knowledge_type", KNOWLEDGE_TYPE, nullable=False),
        sa.Column("state", CARD_STATE, server_default="learning", nullable=False),
        sa.Column("step", sa.Integer(), nullable=True),
        sa.Column("stability", sa.Float(), nullable=True),
        sa.Column("difficulty", sa.Float(), nullable=True),
        sa.Column("due", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_review", sa.TIMESTAMP(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_memory_card"),
        sa.UniqueConstraint(
            "learner_id",
            "lexeme_id",
            "knowledge_type",
            name="uq_memory_card_learner_id_lexeme_id_knowledge_type",
        ),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_memory_card_learner_id_learner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lexeme_id"],
            ["lexeme.id"],
            name="fk_memory_card_lexeme_id_lexeme",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_memory_card_learner_id_due", "memory_card", ["learner_id", "due"])

    op.create_table(
        "word_context",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("lexeme_id", sa.Integer(), nullable=False),
        sa.Column("sentence", sa.Text(), nullable=False),
        sa.Column("topic", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_word_context"),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_word_context_learner_id_learner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lexeme_id"],
            ["lexeme.id"],
            name="fk_word_context_lexeme_id_lexeme",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_word_context_learner_id_lexeme_id", "word_context", ["learner_id", "lexeme_id"]
    )

    op.create_table(
        "review_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("rating", RATING, nullable=False),
        sa.Column("source", REVIEW_SOURCE, nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_review_log"),
        sa.ForeignKeyConstraint(
            ["card_id"],
            ["memory_card.id"],
            name="fk_review_log_card_id_memory_card",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_review_log_card_id", "review_log", ["card_id"])


def downgrade() -> None:
    op.drop_table("review_log")
    op.drop_table("word_context")
    op.drop_table("memory_card")
    op.drop_table("learner_lexeme")
    op.drop_table("lexeme")
    op.drop_table("learner")

    bind = op.get_bind()
    for enum in reversed(ENUMS):
        enum.drop(bind)
