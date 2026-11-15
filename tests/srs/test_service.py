from datetime import UTC, datetime, timedelta

import fsrs
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from soltura.learner.models import (
    CardState,
    KnowledgeType,
    Learner,
    LearnerLexeme,
    Lexeme,
    LexemeOrigin,
    LexemeStatus,
    MemoryCard,
    Rating,
    ReviewLog,
    ReviewSource,
    UnitKind,
    WordContext,
)
from soltura.srs.service import (
    MAX_TRANSLATION_LENGTH,
    due_queue,
    interleave,
    review,
    save_word,
)
from tests.factories import MemoryCardFactory

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


async def test_saving_a_word_creates_both_cards_due_now(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None and lexemes[2].id is not None
    cards = await save_word(
        session, learner.id, lexemes[2].id, sentence="Aunque llueve, salimos.", now=NOW
    )

    assert sorted(card.knowledge_type for card in cards) == [
        KnowledgeType.RECALL,
        KnowledgeType.RECOGNIZE,
    ]
    assert all(card.due == NOW and card.state == CardState.LEARNING for card in cards)
    assert all(card.step == 0 for card in cards)
    assert all(card.unit_kind == UnitKind.WORD for card in cards)
    assert all(card.unit_key == str(lexemes[2].id) for card in cards)
    assert all(card.stability is None and card.difficulty is None for card in cards)
    status = (await session.execute(select(LearnerLexeme.status))).scalar_one()
    assert status == LexemeStatus.LEARNING


async def test_saving_a_word_again_keeps_its_cards_and_adds_the_sentence(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None and lexemes[2].id is not None
    first = await save_word(session, learner.id, lexemes[2].id, "Aunque llueve, salimos.", NOW)
    second = await save_word(
        session, learner.id, lexemes[2].id, "Aunque es tarde, sigo.", NOW + timedelta(days=1)
    )

    assert [card.id for card in second] == [card.id for card in first]
    assert all(card.due == NOW for card in second)
    sentences = (await session.execute(select(WordContext.sentence))).scalars().all()
    assert sorted(sentences) == ["Aunque es tarde, sigo.", "Aunque llueve, salimos."]


async def test_a_good_review_moves_due_forward_and_logs_it(
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    scheduler: fsrs.Scheduler,
) -> None:
    assert learner.id is not None and lexemes[0].id is not None
    card, _ = await save_word(session, learner.id, lexemes[0].id, "Es tarde.", NOW)

    await review(
        session,
        card,
        Rating.GOOD,
        ReviewSource.WARMUP,
        NOW,
        answer="ser",
        duration_ms=2400,
        scheduler=scheduler,
    )

    assert card.due > NOW
    assert card.last_review == NOW
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [(log.card_id, log.rating, log.source, log.answer) for log in logs] == [
        (card.id, Rating.GOOD, ReviewSource.WARMUP, "ser")
    ]


@pytest.mark.parametrize("rating", [Rating.GOOD, Rating.AGAIN])
async def test_the_first_answer_schedules_a_new_card_days_ahead_not_minutes(
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    scheduler: fsrs.Scheduler,
    rating: Rating,
) -> None:
    assert learner.id is not None and lexemes[0].id is not None
    card, _ = await save_word(session, learner.id, lexemes[0].id, "Es tarde.", NOW)

    await review(session, card, rating, ReviewSource.WARMUP, NOW, scheduler=scheduler)

    assert card.state == CardState.REVIEW
    assert card.due >= NOW + timedelta(days=1)


async def test_reviews_follow_the_fsrs_schedule(
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    scheduler: fsrs.Scheduler,
) -> None:
    assert learner.id is not None and lexemes[0].id is not None
    card, _ = await save_word(session, learner.id, lexemes[0].id, "Es tarde.", NOW)
    expected = fsrs.Card(card_id=card.id, due=NOW)
    moments = [NOW, NOW + timedelta(minutes=10), NOW + timedelta(days=3)]

    for moment in moments:
        await review(session, card, Rating.GOOD, ReviewSource.WARMUP, moment, scheduler=scheduler)
        expected, _ = scheduler.review_card(expected, fsrs.Rating.Good, moment)
        await session.refresh(card)

    assert card.due == expected.due
    assert card.stability == pytest.approx(expected.stability)
    assert card.state == CardState.REVIEW


async def test_reviewing_an_unsaved_card_is_refused(session: AsyncSession) -> None:
    card = MemoryCardFactory.build(id=None)

    with pytest.raises(ValueError):
        await review(session, card, Rating.GOOD, ReviewSource.WARMUP, NOW)


async def test_the_due_queue_never_shows_one_words_cards_back_to_back(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    for lexeme in lexemes:
        assert lexeme.id is not None
        await save_word(session, learner.id, lexeme.id, f"Frase con {lexeme.lemma}.", NOW)

    queue = await due_queue(session, learner.id, now=NOW, limit=10, unit_kind=UnitKind.WORD)

    assert len(queue) == 6
    assert all(a.unit_key != b.unit_key for a, b in zip(queue, queue[1:], strict=False))


async def test_the_word_queue_leaves_out_other_units(
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    due_conjugation_card: MemoryCard,
) -> None:
    assert learner.id is not None and lexemes[0].id is not None
    await save_word(session, learner.id, lexemes[0].id, "Es tarde.", NOW)

    words = await due_queue(session, learner.id, now=NOW, limit=10, unit_kind=UnitKind.WORD)
    conjugations = await due_queue(
        session, learner.id, now=NOW, limit=10, unit_kind=UnitKind.CONJUGATION
    )

    assert {card.unit_kind for card in words} == {UnitKind.WORD}
    assert len(words) == 2
    assert [card.id for card in conjugations] == [due_conjugation_card.id]


def test_interleave_alternates_knowledge_types_when_it_can() -> None:
    cards = [
        MemoryCardFactory.build(id=i, lexeme_id=lexeme_id, knowledge_type=knowledge_type)
        for i, (lexeme_id, knowledge_type) in enumerate(
            [
                (1, KnowledgeType.RECOGNIZE),
                (2, KnowledgeType.RECOGNIZE),
                (1, KnowledgeType.RECALL),
                (2, KnowledgeType.RECALL),
            ]
        )
    ]

    ordered = interleave(cards)

    assert [(card.unit_key, card.knowledge_type) for card in ordered] == [
        ("1", KnowledgeType.RECOGNIZE),
        ("2", KnowledgeType.RECALL),
        ("1", KnowledgeType.RECALL),
        ("2", KnowledgeType.RECOGNIZE),
    ]


async def test_the_due_queue_leaves_out_cards_not_yet_due(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme], scheduler: fsrs.Scheduler
) -> None:
    assert learner.id is not None and lexemes[0].id is not None
    card, other = await save_word(session, learner.id, lexemes[0].id, "Es tarde.", NOW)
    await review(session, card, Rating.GOOD, ReviewSource.WARMUP, NOW, scheduler=scheduler)

    queue = await due_queue(session, learner.id, now=NOW, limit=10, unit_kind=UnitKind.WORD)

    assert [queued.id for queued in queue] == [other.id]
    assert (
        await session.execute(select(MemoryCard.id).where(col(MemoryCard.due) > NOW))
    ).scalars().all() == [card.id]


async def test_saving_a_known_word_marks_it_as_learning(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None and lexemes[1].id is not None
    session.add(
        LearnerLexeme(
            learner_id=learner.id,
            lexeme_id=lexemes[1].id,
            status=LexemeStatus.KNOWN,
            origin=LexemeOrigin.ONBOARDING,
        )
    )
    await session.flush()

    await save_word(session, learner.id, lexemes[1].id, "Estoy en casa.", NOW)

    session.expire_all()
    row = (await session.execute(select(LearnerLexeme))).scalar_one()
    assert (row.status, row.origin) == (LexemeStatus.LEARNING, LexemeOrigin.ONBOARDING)


async def test_forgetting_a_reviewed_card_sends_it_to_relearning(
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    scheduler: fsrs.Scheduler,
) -> None:
    assert learner.id is not None and lexemes[0].id is not None
    card, _ = await save_word(session, learner.id, lexemes[0].id, "Es tarde.", NOW)
    await review(session, card, Rating.GOOD, ReviewSource.WARMUP, NOW, scheduler=scheduler)
    assert card.state == CardState.REVIEW

    await review(
        session,
        card,
        Rating.AGAIN,
        ReviewSource.WARMUP,
        NOW + timedelta(days=3),
        scheduler=scheduler,
    )

    card_id = card.id
    session.expire_all()
    stored = await session.get(MemoryCard, card_id)
    assert stored is not None
    assert stored.state == CardState.RELEARNING
    assert stored.due < NOW + timedelta(days=4)


async def _kept_translation(session: AsyncSession) -> str | None:
    kept: str | None = (await session.execute(select(LearnerLexeme.translation))).scalar_one()
    return kept


async def test_a_saved_word_keeps_its_translation_and_saving_it_again_does_not_replace_it(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None and lexemes[1].id is not None

    await save_word(session, learner.id, lexemes[1].id, "Estoy en casa.", NOW, None, " estar ")
    first = await _kept_translation(session)
    await save_word(session, learner.id, lexemes[1].id, "Estoy bien.", NOW, None, "бути")

    assert (first, await _kept_translation(session)) == ("estar", "estar")
    assert len((await session.execute(select(MemoryCard))).scalars().all()) == 2


async def test_saving_a_word_again_fills_a_translation_it_never_had(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None and lexemes[1].id is not None
    await save_word(session, learner.id, lexemes[1].id, "Estoy en casa.", NOW)

    assert await _kept_translation(session) is None
    await save_word(session, learner.id, lexemes[1].id, "Estoy bien.", NOW, None, "бути")

    assert await _kept_translation(session) == "бути"


@pytest.mark.parametrize(
    ("given", "kept"),
    [
        ("  ", None),
        ("", None),
        (None, None),
        ("x" * (MAX_TRANSLATION_LENGTH + 50), "x" * MAX_TRANSLATION_LENGTH),
    ],
    ids=["blank", "empty", "none", "long"],
)
async def test_a_blank_translation_is_none_and_a_long_one_is_cut_to_the_column(
    session: AsyncSession,
    learner: Learner,
    lexemes: list[Lexeme],
    given: str | None,
    kept: str | None,
) -> None:
    assert learner.id is not None and lexemes[1].id is not None

    await save_word(session, learner.id, lexemes[1].id, "Estoy en casa.", NOW, None, given)

    assert await _kept_translation(session) == kept
