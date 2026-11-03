from polyfactory.decorators import post_generated
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from soltura.learner.models import Learner, LearnerLexeme, Lexeme, MemoryCard, UnitKind


class LearnerFactory(SQLAlchemyFactory[Learner]):
    __model__ = Learner
    __set_primary_key__ = False


class LexemeFactory(SQLAlchemyFactory[Lexeme]):
    __model__ = Lexeme
    __set_primary_key__ = False


class LearnerLexemeFactory(SQLAlchemyFactory[LearnerLexeme]):
    __model__ = LearnerLexeme
    __set_primary_key__ = False


class MemoryCardFactory(SQLAlchemyFactory[MemoryCard]):
    __model__ = MemoryCard
    __set_primary_key__ = False

    # A card is a word card unless a test says otherwise, keyed the way save_word keys it.
    unit_kind = UnitKind.WORD

    @post_generated
    @classmethod
    def unit_key(cls, lexeme_id: int | None) -> str | None:
        return None if lexeme_id is None else str(lexeme_id)
