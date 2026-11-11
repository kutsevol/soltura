import random
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.language.frequency import UNRANKED
from soltura.language.nlp import analyze
from soltura.learner.models import (
    GistResult,
    KnowledgeType,
    Learner,
    Lexeme,
    MemoryCard,
    Rating,
    ReadingText,
    ReviewLog,
    ReviewSource,
)
from soltura.learner.repository import get_recent_titles, save_placement_run, save_reading_text
from soltura.reading.service import GeneratedText, GistVerdict, Gloss
from soltura.reading.topics import TOPICS
from soltura.reading.variation import FORMS, NAMES
from soltura.srs.service import save_word
from soltura.use_cases.reading import (
    check_gist,
    prepare_text,
    reading_progress,
    save_tapped_word,
    tap_word,
)
from tests.conftest import EASY_TEXT, HARD_TEXT, KnowFn, RankFn
from tests.factories import LexemeFactory
from tests.fakes import FakeLLM

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


async def test_the_prompt_names_the_vocabulary_range_from_the_placement_run(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    assert learner.id is not None
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    await save_placement_run(session, learner.id, 1000, [])
    llm.answer(EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert "knows about the 1,000 most frequent Spanish words" in llm.prompts[0]
    assert "A2" not in llm.prompts[0]


async def test_without_a_placement_run_the_prompt_names_the_baseline_range(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert "knows about the 3,000 most frequent Spanish words" in llm.prompts[0]


async def test_a_learner_who_passed_no_band_is_measured_against_the_first_band(
    session: AsyncSession, learner: Learner, llm: FakeLLM, rank_text: RankFn
) -> None:
    assert learner.id is not None
    # Ranked inside the baseline of 3,000 but outside the first band of 250.
    await rank_text(f"{EASY_TEXT.title}. {EASY_TEXT.text}", 1000)
    await save_placement_run(session, learner.id, 0, [])
    llm.answer(EASY_TEXT, EASY_TEXT, EASY_TEXT)

    prepared = await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert (prepared.coverage, prepared.below_target) == (0.0, True)
    assert "knows about the 250 most frequent Spanish words" in llm.prompts[0]


async def test_a_preset_topic_gets_a_situation_a_form_and_a_name_from_the_lists(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)
    topic = TOPICS[0]

    await prepare_text(session, llm, learner, NOW, topic=topic.prompt, rng=random.Random(3))

    prompt = llm.prompts[0]
    assert sum(situation in prompt for situation in topic.situations) == 1
    assert sum(form in prompt for form in FORMS) == 1
    assert sum(f"call them {name}" in prompt for name in NAMES) == 1


async def test_two_seeds_send_different_prompts_for_the_same_topic(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT, EASY_TEXT)

    for seed in (1, 2):
        await prepare_text(
            session, llm, learner, NOW, topic=TOPICS[2].prompt, rng=random.Random(seed)
        )

    assert llm.prompts[0] != llm.prompts[1]


async def test_the_titles_of_the_last_five_texts_are_asked_not_to_repeat(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    assert learner.id is not None
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    for number in range(1, 7):
        await save_reading_text(session, learner.id, "la playa", f"Título {number}")
    llm.answer(EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert (
        "Do not repeat these recent texts: Título 6; Título 5; Título 4; Título 3; Título 2."
        in (llm.prompts[0])
    )
    assert "Título 1" not in llm.prompts[0]


async def test_a_prepared_text_saves_its_title(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    assert learner.id is not None
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert await get_recent_titles(session, learner.id, 5) == [EASY_TEXT.title]


async def test_a_free_topic_is_varied_without_a_situation(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="la playa")

    assert "Write it as" in llm.prompts[0]
    assert "Situation:" not in llm.prompts[0]


async def test_adapting_a_pasted_text_is_not_varied(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(EASY_TEXT)

    await prepare_text(session, llm, learner, NOW, topic="", source_text="El Ayuntamiento informa.")

    assert "Write it as" not in llm.prompts[0]
    assert "Do not repeat" not in llm.prompts[0]


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
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    llm: FakeLLM,
    reading_text: ReadingText,
) -> None:
    assert learner.id is not None and lexemes[2].id is not None and reading_text.id is not None
    await save_word(session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", NOW)
    llm.answer(Gloss(lemma="Aunque", translation="хоча"))

    result = await tap_word(
        session, llm, learner.id, reading_text.id, "Aunque", "Aunque es tarde, sigo.", NOW
    )

    assert (result.lemma, result.translation, result.reviewed) == ("aunque", "хоча", True)
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [(log.rating, log.source) for log in logs] == [(Rating.AGAIN, ReviewSource.READING_TAP)]
    reviewed = await session.get(MemoryCard, logs[0].card_id)
    assert reviewed is not None and reviewed.knowledge_type == KnowledgeType.RECOGNIZE


async def test_tapping_a_word_that_is_not_due_writes_no_review(
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    llm: FakeLLM,
    reading_text: ReadingText,
) -> None:
    assert learner.id is not None and reading_text.id is not None
    llm.answer(Gloss(lemma="estar", translation="бути, перебувати"))

    result = await tap_word(
        session, llm, learner.id, reading_text.id, "estoy", "Estoy en casa.", NOW
    )

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


async def test_the_gist_check_sends_the_text_and_the_answer_and_returns_the_verdict(
    session: AsyncSession, learner: Learner, llm: FakeLLM, reading_text: ReadingText
) -> None:
    assert learner.id is not None and reading_text.id is not None
    llm.answer(GistVerdict(verdict="partly", reason="Текст про пляж."))

    verdict = await check_gist(
        session, llm, learner.id, reading_text.id, EASY_TEXT.text, "Про сонце"
    )

    assert (verdict.verdict, verdict.reason) == ("partly", "Текст про пляж.")
    assert f"<text>\n{EASY_TEXT.text}\n</text>" in llm.prompts[0]
    assert "<answer>\nПро сонце\n</answer>" in llm.prompts[0]


async def test_a_text_keeps_the_verdict_of_the_first_answer(
    session: AsyncSession, learner: Learner, llm: FakeLLM, reading_text: ReadingText
) -> None:
    assert learner.id is not None and reading_text.id is not None
    llm.answer(
        GistVerdict(verdict="missed", reason="Текст про пляж."),
        GistVerdict(verdict="understood", reason="Текст про пляж."),
    )

    await check_gist(session, llm, learner.id, reading_text.id, EASY_TEXT.text, "Про ліс")
    second = await check_gist(
        session, llm, learner.id, reading_text.id, EASY_TEXT.text, "Про день на пляжі"
    )

    await session.refresh(reading_text)
    assert second.verdict == "understood"
    assert reading_text.gist == GistResult.MISSED


async def test_every_tap_on_a_text_is_counted(
    session: AsyncSession, learner: Learner, llm: FakeLLM, reading_text: ReadingText
) -> None:
    assert learner.id is not None and reading_text.id is not None
    llm.answer(*[Gloss(lemma="estar", translation="бути")] * 3)

    for _ in range(3):
        await tap_word(session, llm, learner.id, reading_text.id, "estoy", "Estoy aquí.", NOW)

    await session.refresh(reading_text)
    assert reading_text.taps == 3


async def test_another_learners_text_is_refused_before_the_model_is_asked(
    session: AsyncSession, learner: Learner, llm: FakeLLM, other_reading_text: ReadingText
) -> None:
    assert learner.id is not None and other_reading_text.id is not None

    with pytest.raises(PermissionError):
        await tap_word(session, llm, learner.id, other_reading_text.id, "estoy", "Estoy.", NOW)
    with pytest.raises(PermissionError):
        await check_gist(session, llm, learner.id, other_reading_text.id, "Texto", "Про щось")

    assert llm.prompts == []


async def test_a_text_prepared_below_the_target_is_saved_as_such(
    session: AsyncSession, learner: Learner, llm: FakeLLM, know: KnowFn
) -> None:
    await know(f"{EASY_TEXT.title}. {EASY_TEXT.text}")
    llm.answer(HARD_TEXT, HARD_TEXT, HARD_TEXT)

    prepared = await prepare_text(session, llm, learner, NOW, topic="la playa")

    saved = await session.get(ReadingText, prepared.text_id)
    assert saved is not None and saved.below_target is True


async def test_reading_progress_scores_the_answered_texts_and_lists_them(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    for gist in (GistResult.UNDERSTOOD, GistResult.PARTLY, GistResult.MISSED):
        text = await save_reading_text(session, learner.id, None, "Un texto")
        text.gist = gist
    await save_reading_text(session, learner.id, None, "Sin respuesta")

    progress = await reading_progress(session, learner.id)

    assert progress.score.percent == 50
    assert [text.gist for text in progress.texts] == [
        GistResult.MISSED,
        GistResult.PARTLY,
        GistResult.UNDERSTOOD,
    ]
