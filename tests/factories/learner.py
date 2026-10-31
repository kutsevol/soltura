from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from soltura.learner.models import Learner, Lexeme, MemoryCard


class LearnerFactory(SQLAlchemyFactory[Learner]):
    __model__ = Learner
    __set_primary_key__ = False


class LexemeFactory(SQLAlchemyFactory[Lexeme]):
    __model__ = Lexeme
    __set_primary_key__ = False


class MemoryCardFactory(SQLAlchemyFactory[MemoryCard]):
    __model__ = MemoryCard
    __set_primary_key__ = False
