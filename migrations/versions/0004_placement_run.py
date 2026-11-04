from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLACEMENT_RUN = "placement_run"


def upgrade() -> None:
    op.create_table(
        PLACEMENT_RUN,
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("known_rank", sa.Integer(), nullable=False),
        sa.Column("bands", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_placement_run"),
        sa.ForeignKeyConstraint(
            ["learner_id"],
            ["learner.id"],
            name="fk_placement_run_learner_id_learner",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_placement_run_learner_id", PLACEMENT_RUN, ["learner_id"])


def downgrade() -> None:
    op.drop_table(PLACEMENT_RUN)
