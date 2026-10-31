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
    WordContext,
)
from soltura.srs.service import due_queue, interleave, review, save_word
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

    queue = await due_queue(session, learner.id, now=NOW, limit=10)

    assert len(queue) == 6
    assert all(a.lexeme_id != b.lexeme_id for a, b in zip(queue, queue[1:], strict=False))


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

    assert [(card.lexeme_id, card.knowledge_type) for card in ordered] == [
        (1, KnowledgeType.RECOGNIZE),
        (2, KnowledgeType.RECALL),
        (1, KnowledgeType.RECALL),
        (2, KnowledgeType.RECOGNIZE),
    ]


async def test_the_due_queue_leaves_out_cards_not_yet_due(
    session: AsyncSession, learner: Learner, lexemes: list[Lexeme], scheduler: fsrs.Scheduler
) -> None:
    assert learner.id is not None and lexemes[0].id is not None
    card, other = await save_word(session, learner.id, lexemes[0].id, "Es tarde.", NOW)
    await review(session, card, Rating.GOOD, ReviewSource.WARMUP, NOW, scheduler=scheduler)

    queue = await due_queue(session, learner.id, now=NOW, limit=10)

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
    for moment in [NOW, NOW + timedelta(minutes=10)]:
        await review(session, card, Rating.GOOD, ReviewSource.WARMUP, moment, scheduler=scheduler)
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
