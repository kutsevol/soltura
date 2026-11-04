from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PLACEMENT_RUN = "placement_run"


def upgrade() -> None:
    op.add_column(PLACEMENT_RUN, sa.Column("items", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column(PLACEMENT_RUN, "items")
