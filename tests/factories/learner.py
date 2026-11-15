from uuid import uuid4

from polyfactory.decorators import post_generated
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from soltura.learner.models import (
    Learner,
    LearnerLexeme,
    Lexeme,
    MemoryCard,
    ReadingText,
    UnitKind,
)


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
    def unit_key(cls, lexeme_id: int | None) -> str:
        # A card of another unit has no lexeme; a test that cares about its key gives one.
        return str(lexeme_id) if lexeme_id is not None else f"unit-{uuid4().hex[:12]}"


class ReadingTextFactory(SQLAlchemyFactory[ReadingText]):
    __model__ = ReadingText
    __set_primary_key__ = False

    topic = None
    gist = None
    taps = 0
    below_target = False
