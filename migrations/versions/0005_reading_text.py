from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

READING_TEXT = "reading_text"


def upgrade() -> None:
    op.create_table(
        READING_TEXT,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("topic", sa.String(200), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_reading_text"),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_reading_text_learner_id_learner",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_reading_text_learner_id", READING_TEXT, ["learner_id"])


def downgrade() -> None:
    op.drop_table(READING_TEXT)
