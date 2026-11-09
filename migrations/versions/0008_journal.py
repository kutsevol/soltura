from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JOURNAL_ENTRY = "journal_entry"
ERROR_LOG = "error_log"
ERROR_KIND = postgresql.ENUM(
    "grammar", "vocabulary", "spelling", "other", name="error_kind", create_type=False
)


def _created_at() -> sa.Column:
    return sa.Column(
        "created_at",
        sa.TIMESTAMP(timezone=True),
        server_default=sa.text("now()"),
        nullable=False,
    )


def upgrade() -> None:
    ERROR_KIND.create(op.get_bind())
    op.create_table(
        JOURNAL_ENTRY,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.String(200), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("corrected", sa.Text(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_journal_entry"),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_journal_entry_learner_id_learner",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_journal_entry_learner_id", JOURNAL_ENTRY, ["learner_id"])
    op.create_table(
        ERROR_LOG,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entry_id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("kind", ERROR_KIND, nullable=False),
        sa.Column("unit_id", sa.String(64), nullable=True),
        sa.Column("original", sa.Text(), nullable=False),
        sa.Column("corrected", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id", name="pk_error_log"),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            [f"{JOURNAL_ENTRY}.id"],
            name="fk_error_log_entry_id_journal_entry",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_error_log_learner_id_learner",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_error_log_entry_id", ERROR_LOG, ["entry_id"])
    op.create_index("ix_error_log_learner_id", ERROR_LOG, ["learner_id"])


def downgrade() -> None:
    op.drop_table(ERROR_LOG)
    op.drop_table(JOURNAL_ENTRY)
    ERROR_KIND.drop(op.get_bind())
