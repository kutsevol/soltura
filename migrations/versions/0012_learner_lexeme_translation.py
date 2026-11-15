from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEARNER_LEXEME = "learner_lexeme"


def upgrade() -> None:
    op.add_column(LEARNER_LEXEME, sa.Column("translation", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column(LEARNER_LEXEME, "translation")
