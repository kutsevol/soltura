from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MEMORY_CARD = "memory_card"
LEXEME_UNIQUE = "uq_memory_card_learner_id_lexeme_id_knowledge_type"

memory_card = sa.table(
    MEMORY_CARD,
    sa.column("lexeme_id", sa.Integer()),
    sa.column("unit_key", sa.String()),
)


def upgrade() -> None:
    # A word card that somehow has no key is keyed by its lexeme, as the first migration did,
    # so the NOT NULL below cannot fail on a late row.
    op.execute(
        memory_card.update()
        .where(memory_card.c.unit_key.is_(None), memory_card.c.lexeme_id.is_not(None))
        .values(unit_key=sa.cast(memory_card.c.lexeme_id, sa.String()))
    )
    op.alter_column(MEMORY_CARD, "unit_key", existing_type=sa.String(64), nullable=False)
    # The unit key is unique per learner, kind and knowledge type, and a word's key is its
    # lexeme: the constraint on the lexeme says nothing the key's does not.
    op.drop_constraint(LEXEME_UNIQUE, MEMORY_CARD, type_="unique")


def downgrade() -> None:
    op.create_unique_constraint(
        LEXEME_UNIQUE, MEMORY_CARD, ["learner_id", "lexeme_id", "knowledge_type"]
    )
    op.alter_column(MEMORY_CARD, "unit_key", existing_type=sa.String(64), nullable=True)
