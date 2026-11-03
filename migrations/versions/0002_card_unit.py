from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UNIT_KIND = postgresql.ENUM("word", "conjugation", "grammar", name="unit_kind", create_type=False)

MEMORY_CARD = "memory_card"
UNIT_UNIQUE = "uq_memory_card_learner_id_unit_kind_unit_key_knowledge_type"

memory_card = sa.table(
    MEMORY_CARD,
    sa.column("lexeme_id", sa.Integer()),
    sa.column("unit_key", sa.String()),
)


def upgrade() -> None:
    UNIT_KIND.create(op.get_bind())
    op.add_column(
        MEMORY_CARD,
        sa.Column("unit_kind", UNIT_KIND, server_default="word", nullable=False),
    )
    op.add_column(MEMORY_CARD, sa.Column("unit_key", sa.String(64), nullable=True))
    # Every card that exists today is a word card, keyed by its lexeme.
    op.execute(memory_card.update().values(unit_key=sa.cast(memory_card.c.lexeme_id, sa.String())))
    op.alter_column(MEMORY_CARD, "lexeme_id", existing_type=sa.Integer(), nullable=True)
    op.create_unique_constraint(
        UNIT_UNIQUE, MEMORY_CARD, ["learner_id", "unit_kind", "unit_key", "knowledge_type"]
    )


def downgrade() -> None:
    # Only word cards have a lexeme, so the cards of other units cannot survive the
    # return to a lexeme-only table.
    op.execute(memory_card.delete().where(memory_card.c.lexeme_id.is_(None)))
    op.drop_constraint(UNIT_UNIQUE, MEMORY_CARD, type_="unique")
    op.alter_column(MEMORY_CARD, "lexeme_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column(MEMORY_CARD, "unit_key")
    op.drop_column(MEMORY_CARD, "unit_kind")
    UNIT_KIND.drop(op.get_bind())
