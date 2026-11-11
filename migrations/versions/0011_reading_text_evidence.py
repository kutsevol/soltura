from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

READING_TEXT = "reading_text"
GIST_RESULT = postgresql.ENUM("understood", "partly", "missed", name="gist_result", create_type=False)


def upgrade() -> None:
    GIST_RESULT.create(op.get_bind())
    op.add_column(READING_TEXT, sa.Column("gist", GIST_RESULT, nullable=True))
    op.add_column(
        READING_TEXT, sa.Column("taps", sa.Integer(), server_default=sa.text("0"), nullable=False)
    )
    op.add_column(
        READING_TEXT,
        sa.Column("below_target", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column(READING_TEXT, "below_target")
    op.drop_column(READING_TEXT, "taps")
    op.drop_column(READING_TEXT, "gist")
    GIST_RESULT.drop(op.get_bind())
