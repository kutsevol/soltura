from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.community.postgres import PostgresContainer

from soltura.app import create_app
from soltura.config import settings
from soltura.db import get_session
from soltura.language.frequency import BANDS, UNRANKED
from soltura.language.nlp import analyze
from soltura.learner.models import (
    KnowledgeType,
    Learner,
    LearnerLexeme,
    Lexeme,
    LexemeOrigin,
    LexemeStatus,
    MemoryCard,
    PlacementRun,
    UnitKind,
)
from soltura.learner.repository import save_placement_run
from soltura.llm.client import Effort, SchemaT, get_llm
from soltura.onboarding.service import PlacementSentence, PlacementSentences
from soltura.practice.checking import TranslationVerdict
from soltura.reading.service import GeneratedText
from soltura.srs.service import save_word
from tests.factories import (
    LearnerFactory,
    LearnerLexemeFactory,
    LexemeFactory,
    MemoryCardFactory,
)
from tests.fakes import FakeLLM

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    with PostgresContainer("postgres:17-alpine", driver="asyncpg") as postgres:
        url = postgres.get_connection_url()
        alembic_config = Config(ROOT / "alembic.ini")
        alembic_config.set_main_option("sqlalchemy.url", url)
        command.upgrade(alembic_config, "head")
        yield url


@pytest.fixture
async def session(database_url: str) -> AsyncIterator[AsyncSession]:
    # Each test runs inside one outer transaction that is rolled back on teardown;
    # commits in the code under test become savepoints, so no test sees another's rows.
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        ) as session:
            yield session
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def learner_client(
    session: AsyncSession, learner: Learner, llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
) -> AsyncIterator[AsyncClient]:
    monkeypatch.setattr(settings.auth, "dev_telegram_user_id", learner.telegram_user_id)
    app = create_app()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_llm] = lambda: llm
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
async def learner(session: AsyncSession) -> Learner:
    learner = LearnerFactory.build()
    session.add(learner)
    await session.flush()
    return learner


@pytest.fixture
async def lexemes(session: AsyncSession) -> list[Lexeme]:
    lexemes = [
        LexemeFactory.build(lemma=lemma, frequency_rank=rank)
        for rank, lemma in enumerate(["ser", "estar", "aunque"], start=1)
    ]
    session.add_all(lexemes)
    await session.flush()
    return lexemes


@pytest.fixture
async def vocabulary_lexemes(session: AsyncSession) -> dict[str, Lexeme]:
    ranks = {
        "known": (10, "VERB"),
        "learning": (20, "NOUN"),
        "unmet": (30, "ADJ"),
        "name": (40, "PROPN"),
        "second_band": (300, "NOUN"),
        "tail": (9_000, "NOUN"),
        "unranked": (UNRANKED, "X"),
    }
    lexemes = {
        lemma: LexemeFactory.build(lemma=lemma, pos=pos, frequency_rank=rank)
        for lemma, (rank, pos) in ranks.items()
    }
    session.add_all(lexemes.values())
    await session.flush()
    return lexemes


@pytest.fixture
async def vocabulary_words(
    session: AsyncSession, learner: Learner, vocabulary_lexemes: dict[str, Lexeme]
) -> None:
    other = LearnerFactory.build()
    session.add(other)
    await session.flush()
    assert learner.id is not None and other.id is not None
    owned = [
        (learner.id, "known", LexemeStatus.KNOWN),
        (learner.id, "learning", LexemeStatus.LEARNING),
        (learner.id, "name", LexemeStatus.KNOWN),
        (learner.id, "second_band", LexemeStatus.KNOWN),
        (learner.id, "unranked", LexemeStatus.LEARNING),
        (other.id, "unmet", LexemeStatus.KNOWN),
    ]
    session.add_all(
        LearnerLexemeFactory.build(
            learner_id=learner_id,
            lexeme_id=vocabulary_lexemes[lemma].id,
            status=status,
            origin=LexemeOrigin.READING,
        )
        for learner_id, lemma, status in owned
    )
    await session.flush()


@pytest.fixture
def llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture
async def due_conjugation_card(session: AsyncSession, learner: Learner) -> MemoryCard:
    # Due long before any test's clock, and without a lexeme: the shape every
    # non-word card has.
    card = MemoryCardFactory.build(
        learner_id=learner.id,
        unit_kind=UnitKind.CONJUGATION,
        unit_key="tener|preterite|ellos",
        lexeme_id=None,
        knowledge_type=KnowledgeType.RECALL,
        due=datetime(2020, 1, 1, tzinfo=UTC),
    )
    session.add(card)
    await session.flush()
    return card


@pytest.fixture
async def verb_lexemes(session: AsyncSession) -> list[Lexeme]:
    # Everything ahead of ser that must not be offered: a noun, haber, a verb verbecc has
    # no template for and a weather verb. tener follows ser.
    ranked = [
        ("casa", "NOUN"),
        ("haber", "AUX"),
        ("zzzar", "VERB"),
        ("llover", "VERB"),
        ("ser", "AUX"),
        ("tener", "VERB"),
    ]
    lexemes = [
        LexemeFactory.build(lemma=lemma, pos=pos, frequency_rank=rank)
        for rank, (lemma, pos) in enumerate(ranked, start=1)
    ]
    session.add_all(lexemes)
    await session.flush()
    return lexemes


WARMUP_SAVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)


@pytest.fixture
async def saved_aunque(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> dict[KnowledgeType, MemoryCard]:
    assert learner.id is not None and lexemes[2].id is not None
    cards = await save_word(
        session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", WARMUP_SAVED_AT
    )
    return {card.knowledge_type: card for card in cards}


HUB_SAVED_AT = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)
PLACEMENT_BANDS = [{"band": 0, "max_rank": 250, "correct": 5, "total": 5}]


@pytest.fixture
async def saved_word(session: AsyncSession, learner: Learner, lexemes: list[Lexeme]) -> None:
    assert learner.id is not None and lexemes[2].id is not None
    await save_word(session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", HUB_SAVED_AT)


@pytest.fixture
async def placement_run(session: AsyncSession, learner: Learner) -> PlacementRun:
    assert learner.id is not None
    return await save_placement_run(session, learner.id, 500, PLACEMENT_BANDS)


@pytest.fixture
async def failed_placement_run(session: AsyncSession, learner: Learner) -> PlacementRun:
    assert learner.id is not None
    return await save_placement_run(session, learner.id, 0, PLACEMENT_BANDS)


EASY_TEXT = GeneratedText(
    title="Un día de sol", text="Hoy hace sol. Voy a la playa con mi hermano y comemos pan."
)
HARD_TEXT = GeneratedText(
    title="Un día de sol",
    text="Hoy hace sol. El arrendatario impugnó la fianza y el notario redactó un acta.",
)


KnowFn = Callable[[str], Awaitable[None]]
RankFn = Callable[[str, int], Awaitable[None]]


@pytest.fixture
def rank_text(session: AsyncSession) -> RankFn:
    # Creates a lexeme for every lemma of a text at consecutive frequency ranks from
    # `first_rank`, without marking any of them known.
    async def rank(text: str, first_rank: int) -> None:
        lemmas = sorted({token.lemma for token in analyze(text)})
        session.add_all(
            LexemeFactory.build(lemma=lemma, frequency_rank=first_rank + i)
            for i, lemma in enumerate(lemmas)
        )
        await session.flush()

    return rank


@pytest.fixture
def know(session: AsyncSession, learner: Learner) -> KnowFn:
    # Marks every lemma of a text as known to the learner, creating the lexemes.
    async def mark(text: str) -> None:
        assert learner.id is not None
        lemmas = sorted({token.lemma for token in analyze(text)})
        lexemes = [
            LexemeFactory.build(lemma=lemma, frequency_rank=5000 + i)
            for i, lemma in enumerate(lemmas)
        ]
        session.add_all(lexemes)
        await session.flush()
        session.add_all(
            LearnerLexeme(
                learner_id=learner.id,
                lexeme_id=lexeme.id,
                status=LexemeStatus.KNOWN,
                origin=LexemeOrigin.ONBOARDING,
            )
            for lexeme in lexemes
            if lexeme.id is not None
        )
        await session.flush()

    return mark


CORRECT = "так"


class JudgeByAnswer(FakeLLM):
    # Judges a translation as correct when the learner typed CORRECT, so concurrent
    # judging needs no particular call order.
    async def __call__(
        self,
        schema: type[SchemaT],
        system: str,
        prompt: str,
        effort: Effort,
        max_tokens: int = 16_000,
    ) -> SchemaT:
        if schema is TranslationVerdict:
            self.prompts.append(prompt)
            verdict = "correct" if prompt.endswith(f"Learner's answer: {CORRECT}") else "wrong"
            return cast(
                SchemaT,
                TranslationVerdict(verdict=verdict, reason="Пояснення", expected="значення"),
            )
        return await super().__call__(schema, system, prompt, effort, max_tokens)


@pytest.fixture
def judge() -> JudgeByAnswer:
    return JudgeByAnswer()


@pytest.fixture
async def banded_lexemes(session: AsyncSession) -> list[Lexeme]:
    # Ten nouns at the top of every band, two more than the test asks, plus a preposition
    # per band that the
    # placement must never pick.
    lexemes = [
        LexemeFactory.build(lemma=f"word{band}x{i}", pos="NOUN", frequency_rank=max_rank - i)
        for band, (_, max_rank) in enumerate(BANDS)
        for i in range(10)
    ] + [
        LexemeFactory.build(lemma=f"prep{band}", pos="ADP", frequency_rank=min_rank)
        for band, (min_rank, _) in enumerate(BANDS)
    ]
    session.add_all(lexemes)
    await session.flush()
    return lexemes


@pytest.fixture
def sentenced(banded_lexemes: list[Lexeme], judge: JudgeByAnswer) -> None:
    # The model's answer to the sentence request: one sentence and meaning per noun.
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    judge.answer(
        PlacementSentences(
            sentences=[
                PlacementSentence(
                    lemma=lemma,
                    sentence=f"Hoy veo {lemma}.",
                    target_form=lemma,
                    meaning=f"значення {lemma}",
                )
                for lemma in nouns
            ]
        )
    )
