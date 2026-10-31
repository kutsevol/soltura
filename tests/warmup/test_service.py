from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from soltura.learner.models import (
    KnowledgeType,
    Learner,
    MemoryCard,
    Rating,
    ReviewLog,
    ReviewSource,
)
from soltura.llm.client import LLMUnavailableError
from soltura.practice.checking import TranslationVerdict
from soltura.practice.text import split_around
from soltura.warmup.service import (
    ContextSentence,
    WarmupItem,
    answer_item,
    build_warmup,
    recall_before_recognize,
)
from tests.factories import LearnerFactory
from tests.fakes import FakeLLM

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)
RECALL_CONTEXT = ContextSentence(
    sentence="Aunque estoy cansado, voy al gimnasio.",
    target_form="Aunque",
    translation="Хоча я втомлений, я йду в спортзал.",
)
RECOGNIZE_CONTEXT = ContextSentence(
    sentence="Salgo a pasear aunque hace frío.",
    target_form="aunque",
    translation="Я виходжу гуляти, хоча холодно.",
)


async def test_the_warmup_shows_each_due_card_in_a_fresh_sentence(
    session: AsyncSession,
    learner: Learner,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
) -> None:
    assert learner.id is not None
    llm.answer(RECOGNIZE_CONTEXT, RECALL_CONTEXT)

    items = await build_warmup(session, llm, learner.id, NOW)

    # The queue hands out recognize first; recall moves ahead of it for the same word.
    assert [(item.knowledge_type, item.sentence) for item in items] == [
        (KnowledgeType.RECALL, RECALL_CONTEXT.sentence),
        (KnowledgeType.RECOGNIZE, RECOGNIZE_CONTEXT.sentence),
    ]
    assert all(item.sentence != "Aunque llueve, salimos." for item in items)
    assert items[0].translation == RECALL_CONTEXT.translation
    assert "Aunque llueve, salimos." in llm.prompts[0]


async def test_without_a_fresh_sentence_recognize_falls_back_and_recall_waits(
    session: AsyncSession,
    learner: Learner,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
) -> None:
    assert learner.id is not None
    llm.fail(ContextSentence, LLMUnavailableError("Claude returned 529"))
    llm.fail(ContextSentence, LLMUnavailableError("Claude returned 529"))

    items = await build_warmup(session, llm, learner.id, NOW)

    assert [(item.knowledge_type, item.sentence, item.target_form) for item in items] == [
        (KnowledgeType.RECOGNIZE, "Aunque llueve, salimos.", "Aunque")
    ]


async def test_a_generated_sentence_the_learner_has_seen_is_not_reused(
    session: AsyncSession,
    learner: Learner,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
) -> None:
    assert learner.id is not None
    seen = ContextSentence(
        sentence="Aunque llueve, salimos.", target_form="Aunque", translation="Хоча йде дощ."
    )
    llm.answer(seen, RECALL_CONTEXT)

    items = await build_warmup(session, llm, learner.id, NOW)

    # The recognize card's generated sentence repeats the saved one, so it is
    # discarded like a failed generation; the recall card keeps its fresh sentence.
    assert [(item.knowledge_type, item.sentence) for item in items] == [
        (KnowledgeType.RECALL, RECALL_CONTEXT.sentence),
        (KnowledgeType.RECOGNIZE, "Aunque llueve, salimos."),
    ]


async def test_nothing_due_means_an_empty_warmup(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None

    assert await build_warmup(session, llm, learner.id, NOW) == []
    assert llm.prompts == []


def _item(card: MemoryCard, context: ContextSentence) -> WarmupItem:
    assert card.id is not None
    return WarmupItem(
        card_id=card.id,
        knowledge_type=card.knowledge_type,
        lemma="aunque",
        sentence=context.sentence,
        target_form=context.target_form,
        translation=context.translation,
    )


@pytest.mark.parametrize(
    ("answer", "rating"),
    [
        ("aunque", Rating.GOOD),
        ("AUNQUE", Rating.GOOD),
        ("aunqe", Rating.HARD),
        ("pero", Rating.AGAIN),
    ],
)
async def test_a_recall_answer_is_checked_by_code(
    session: AsyncSession,
    learner: Learner,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
    answer: str,
    rating: Rating,
) -> None:
    assert learner.id is not None
    recall = saved_aunque[KnowledgeType.RECALL]

    result = await answer_item(
        session, llm, learner.id, _item(recall, RECALL_CONTEXT), answer, 2100, NOW
    )

    assert result.rating == rating
    logs = (await session.execute(select(ReviewLog))).scalars().all()
    assert [(log.rating, log.source, log.answer, log.duration_ms) for log in logs] == [
        (rating, ReviewSource.WARMUP, answer, 2100)
    ]
    assert llm.prompts == []


async def test_a_recognize_answer_is_judged_by_the_llm(
    session: AsyncSession,
    learner: Learner,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
) -> None:
    assert learner.id is not None
    llm.answer(TranslationVerdict(verdict="partly", reason="Ближче до «але».", expected="хоча"))

    result = await answer_item(
        session,
        llm,
        learner.id,
        _item(saved_aunque[KnowledgeType.RECOGNIZE], RECOGNIZE_CONTEXT),
        "але",
        None,
        NOW,
    )

    assert (result.rating, result.expected) == (Rating.HARD, "хоча")


async def test_giving_up_is_a_failed_review_without_an_answer(
    session: AsyncSession,
    learner: Learner,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
) -> None:
    assert learner.id is not None

    result = await answer_item(
        session,
        llm,
        learner.id,
        _item(saved_aunque[KnowledgeType.RECALL], RECALL_CONTEXT),
        "",
        None,
        NOW,
    )

    assert result.rating == Rating.AGAIN
    log = (await session.execute(select(ReviewLog))).scalar_one()
    assert log.answer is None


async def test_another_learners_card_cannot_be_answered(
    session: AsyncSession, saved_aunque: dict[KnowledgeType, MemoryCard], llm: FakeLLM
) -> None:
    intruder = LearnerFactory.build()
    session.add(intruder)
    await session.flush()
    assert intruder.id is not None

    with pytest.raises(PermissionError):
        await answer_item(
            session,
            llm,
            intruder.id,
            _item(saved_aunque[KnowledgeType.RECALL], RECALL_CONTEXT),
            "aunque",
            None,
            NOW,
        )


def test_a_words_recall_card_comes_before_its_recognize_card() -> None:
    def item(card_id: int, lemma: str, knowledge_type: KnowledgeType) -> WarmupItem:
        return WarmupItem(
            card_id=card_id,
            knowledge_type=knowledge_type,
            lemma=lemma,
            sentence=f"Frase con {lemma}.",
            target_form=lemma,
        )

    queue = [
        item(1, "nieto", KnowledgeType.RECOGNIZE),
        item(2, "ir", KnowledgeType.RECALL),
        item(3, "nieto", KnowledgeType.RECALL),
        item(4, "ir", KnowledgeType.RECOGNIZE),
    ]

    assert [i.card_id for i in recall_before_recognize(queue)] == [3, 2, 1, 4]


@pytest.mark.parametrize(
    ("sentence", "form", "parts"),
    [
        ("Estoy seguro de que es verdad.", "es", ("Estoy seguro de que ", "es", " verdad.")),
        ("Vamos a ir a la playa.", "a", ("Vamos ", "a", " ir a la playa.")),
        ("Aunque llueve, salimos.", "aunque", ("", "Aunque", " llueve, salimos.")),
        ("Estoy en casa.", "es", None),
    ],
)
def test_the_target_form_is_found_only_as_a_whole_word(
    sentence: str, form: str, parts: tuple[str, str, str] | None
) -> None:
    assert split_around(sentence, form) == parts


async def test_a_sentence_holding_the_form_only_inside_another_word_is_discarded(
    session: AsyncSession,
    learner: Learner,
    saved_aunque: dict[KnowledgeType, MemoryCard],
    llm: FakeLLM,
) -> None:
    assert learner.id is not None
    inside = ContextSentence(
        sentence="Aunquemente no existe.", target_form="aunque", translation="Такого слова немає."
    )
    llm.answer(inside, RECALL_CONTEXT)

    items = await build_warmup(session, llm, learner.id, NOW)

    assert [(item.knowledge_type, item.sentence) for item in items] == [
        (KnowledgeType.RECALL, RECALL_CONTEXT.sentence),
        (KnowledgeType.RECOGNIZE, "Aunque llueve, salimos."),
    ]
