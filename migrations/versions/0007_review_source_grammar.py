from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REVIEW_SOURCE = "review_source"
OLD_REVIEW_SOURCE = "review_source_old"
NEW_VALUE = "grammar"
OLD_VALUES = ("warmup", "reading_tap", "conjugation")

review_log = sa.table("review_log", sa.column("source", sa.String()))


def upgrade() -> None:
    op.execute(sa.text(f'ALTER TYPE "{REVIEW_SOURCE}" ADD VALUE IF NOT EXISTS \'{NEW_VALUE}\''))


def downgrade() -> None:
    # Postgres cannot drop a value from an enum, so the type is swapped for one without
    # it; the reviews that used the value have nowhere to go and are deleted first.
    op.execute(review_log.delete().where(sa.cast(review_log.c.source, sa.String()) == NEW_VALUE))
    op.execute(sa.text(f'ALTER TYPE "{REVIEW_SOURCE}" RENAME TO "{OLD_REVIEW_SOURCE}"'))
    postgresql.ENUM(*OLD_VALUES, name=REVIEW_SOURCE).create(op.get_bind())
    op.alter_column(
        "review_log",
        "source",
        existing_type=postgresql.ENUM(name=OLD_REVIEW_SOURCE, create_type=False),
        type_=postgresql.ENUM(*OLD_VALUES, name=REVIEW_SOURCE, create_type=False),
        existing_nullable=False,
        postgresql_using=f'"source"::text::"{REVIEW_SOURCE}"',
    )
    op.execute(sa.text(f'DROP TYPE "{OLD_REVIEW_SOURCE}"'))
