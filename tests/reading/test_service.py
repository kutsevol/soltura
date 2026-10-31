from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.language.nlp import analyze
from soltura.learner.models import (
    KnowledgeType,
    Learner,
    Lexeme,
    MemoryCard,
    Rating,
    ReviewLog,
    ReviewSource,
)
from soltura.reading.service import (
    UNRANKED,
    GeneratedText,
    Gloss,
    prepare_text,
    save_tapped_word,
    split_for_reading,
    tap_word,
)
from soltura.srs.service import save_word
from tests.factories import LexemeFactory
from tests.fakes import FakeLLM
from tests.reading.conftest import EASY_TEXT, HARD_TEXT, KnowFn

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


async def test_a_text_within_coverage_is_accepted_on_the_first_draft(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    prepared = await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert (prepared.attempts, prepared.below_target, prepared.coverage) == (1, False, 1.0)


async def test_a_hard_draft_is_simplified_naming_its_unknown_words(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(HARD_TEXT, EASY_TEXT)

    prepared = await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert (prepared.attempts, prepared.below_target, prepared.text) == (2, False, EASY_TEXT.text)
    assert "arrendatario" in llm.prompts[1]
    assert "fianza" in llm.prompts[1]


async def test_a_text_still_too_hard_after_two_simplifications_is_flagged(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(HARD_TEXT, HARD_TEXT, HARD_TEXT)

    prepared = await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert (prepared.attempts, prepared.below_target) == (3, True)
    assert prepared.coverage < 0.95
    assert len(llm.prompts) == 3


async def test_due_words_are_asked_for_in_the_first_draft(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme], llm: FakeLLM, know: KnowFn
) -> None:
    assert learner.id is not None and lexemes[2].id is not None
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    await save_word(session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", NOW)
    llm.answer(EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert "aunque" in llm.prompts[0]


async def test_without_known_words_the_most_frequent_lemmas_count_as_known(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    lemmas = sorted({token.lemma for token in analyze(f"{EASY_TEXT.title}. {EASY_TEXT.text}")})
    session.add_all(
        LexemeFactory.build(lemma=lemma, frequency_rank=rank)
        for rank, lemma in enumerate(lemmas, start=1)
    )
    await session.flush()
    llm.answer(EASY_TEXT)

    prepared = await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert prepared.coverage == 1.0


async def test_adapting_a_pasted_text_sends_it_as_the_source(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    await prepare_text(
        session, llm, learner, NOW, topic="", source_text="El Ayuntamiento informa de que…"
    )

    assert "<source>\nEl Ayuntamiento informa de que…\n</source>" in llm.prompts[0]


async def test_tapping_a_due_word_records_a_failed_recognition(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme], llm: FakeLLM
) -> None:
    assert learner.id is not None and lexemes[2].id is not None
    await save_word(session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", NOW)
    llm.answer(Gloss(lemma="Aunque", translation="хоча"))

    result = await tap_word(session, llm, learner.id, "Aunque", "Aunque es tarde, sigo.", NOW)

    assert (result.lemma, result.translation, result.reviewed) == ("aunque", "хоча", True)
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [(log.rating, log.source) for log in logs] == [(Rating.AGAIN, ReviewSource.READING_TAP)]
    reviewed = await session.get(MemoryCard, logs[0].card_id)
    assert reviewed is not None and reviewed.knowledge_type == KnowledgeType.RECOGNIZE


async def test_tapping_a_word_that_is_not_due_writes_no_review(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme], llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(Gloss(lemma="estar", translation="бути, перебувати"))

    result = await tap_word(session, llm, learner.id, "estoy", "Estoy en casa.", NOW)

    assert result.reviewed is False
    assert (await session.execute(select(ReviewLog))).scalars().all() == []


async def test_saving_a_tapped_word_uses_its_lemma_and_creates_its_cards(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None

    cards = await save_tapped_word(session, learner.id, "Ser", "La película fue buena.", NOW)

    assert {card.lexeme_id for card in cards} == {lexemes[0].id}
    assert len(cards) == 2


async def test_saving_a_lemma_the_seed_never_ranked_adds_it_unranked(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    cards = await save_tapped_word(
        session, learner.id, "empadronarse", "Hay que empadronarse.", NOW
    )

    lexeme = (
        await session.execute(select(Lexeme).where(col(Lexeme.lemma) == "empadronarse"))
    ).scalar_one()
    assert lexeme.frequency_rank == UNRANKED
    assert {card.lexeme_id for card in cards} == {lexeme.id}


def test_split_for_reading_keeps_each_word_with_its_sentence() -> None:
    paragraphs = split_for_reading("Ayer fue al médico. ¿Qué te dijo?\n\nNada, todo bien.")

    sentences = [["".join(s.text for s in sentence).strip() for sentence in p] for p in paragraphs]
    assert sentences == [["Ayer fue al médico.", "¿Qué te dijo?"], ["Nada, todo bien."]]
    words = [s.text for s in paragraphs[0][1] if s.is_word]
    assert words == ["Qué", "te", "dijo"]


async def test_simplification_names_only_the_rarest_words_over_the_budget(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    session.add_all(
        [
            LexemeFactory.build(lemma="nieto", frequency_rank=3000),
            LexemeFactory.build(lemma="bicicleta", frequency_rank=2500),
        ]
    )
    await session.flush()
    long_text = (
        " ".join([EASY_TEXT.text] * 2) + " Voy con mi nieto, mi bicicleta y mi arrendatario."
    )
    llm.answer(GeneratedText(title=EASY_TEXT.title, text=long_text), EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="la playa")

    named = llm.prompts[1].split(": ", 1)[1].split(". Replace", 1)[0]
    # 39 words allow one unknown: the two rarest go, the more frequent "bicicleta" stays.
    assert named == "arrendatario, nieto"
