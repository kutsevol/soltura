from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

STUDY_SESSION = "study_session"
STUDY_STEP = postgresql.ENUM(
    "warmup", "reading", "grammar", "writing", "done", name="study_step", create_type=False
)


def upgrade() -> None:
    STUDY_STEP.create(op.get_bind())
    op.create_table(
        STUDY_SESSION,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("step", STUDY_STEP, server_default="warmup", nullable=False),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_study_session"),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_study_session_learner_id_learner",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_study_session_learner_id", STUDY_SESSION, ["learner_id"])
    op.create_index(
        "uq_study_session_open",
        STUDY_SESSION,
        ["learner_id"],
        unique=True,
        postgresql_where=sa.text("finished_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_table(STUDY_SESSION)
    STUDY_STEP.drop(op.get_bind())
