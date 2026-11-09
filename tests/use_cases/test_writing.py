from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import (
    ErrorKind,
    KnowledgeType,
    Learner,
    MemoryCard,
    Rating,
    ReviewLog,
    ReviewSource,
)
from soltura.learner.repository import (
    JournalError,
    get_errors_for_entries,
    get_journal_entries,
    get_lexemes_by_lemmas,
    save_journal_entry,
)
from soltura.llm.client import LLMUnavailableError
from soltura.reading.topics import TOPICS
from soltura.srs.service import save_word
from soltura.use_cases.writing import (
    HISTORY_SIZE,
    error_summary,
    journal_history,
    session_prompt,
    submit_entry,
)
from soltura.writing.prompts import PROMPTS
from soltura.writing.service import Correction, FoundError, InvalidText, TextProblem
from tests.conftest import RankFn
from tests.fakes import FakeLLM

NOW = datetime(2026, 11, 9, 8, 0, tzinfo=UTC)
TEXT = "Yo soy cansado porque trabajo mucho."
FIXED = "Estoy cansado porque trabajo mucho."


async def test_a_submitted_text_is_saved_with_its_errors(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(
        Correction(
            corrected_text=FIXED,
            errors=[
                FoundError(original="Yo soy", corrected="Estoy", category="ser_estar", note="Стан.")
            ],
        )
    )

    result = await submit_entry(session, llm, learner.id, PROMPTS[0], f"  {TEXT}\n", NOW)

    entries = await get_journal_entries(session, learner.id, limit=5)
    errors = await get_errors_for_entries(session, [result.entry_id])
    assert [(entry.id, entry.prompt, entry.body, entry.corrected) for entry in entries] == [
        (result.entry_id, PROMPTS[0], TEXT, FIXED)
    ]
    assert [(error.kind, error.unit_id, error.original) for error in errors[result.entry_id]] == [
        (ErrorKind.GRAMMAR, "ser_estar", "Yo soy")
    ]
    assert result.corrected == FIXED
    assert "ser_estar" in llm.prompts[0]


@pytest.mark.parametrize(
    ("text", "problem"),
    [("Hola.", TextProblem.TOO_SHORT), ("a" * 1_001, TextProblem.TOO_LONG)],
)
async def test_a_text_of_the_wrong_length_is_refused_before_the_model_is_called(
    session: AsyncSession, learner: Learner, llm: FakeLLM, text: str, problem: TextProblem
) -> None:
    assert learner.id is not None

    with pytest.raises(InvalidText) as raised:
        await submit_entry(session, llm, learner.id, None, text, NOW)

    assert raised.value.problem == problem
    assert llm.prompts == []


async def test_a_model_failure_saves_nothing(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.fail(Correction, LLMUnavailableError("down"))

    with pytest.raises(LLMUnavailableError):
        await submit_entry(session, llm, learner.id, None, TEXT, NOW)

    assert await get_journal_entries(session, learner.id, limit=5) == []


async def test_a_prompt_that_is_not_one_of_the_tasks_is_not_stored(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    result = await submit_entry(session, llm, learner.id, "forged task", TEXT, NOW)

    assert result.prompt is None


async def test_the_retelling_prompt_of_a_topic_is_stored_with_the_entry(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    prompt = session_prompt(TOPICS[0].label)
    assert prompt is not None
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    result = await submit_entry(session, llm, learner.id, prompt, TEXT, NOW)

    assert result.prompt == prompt


def test_only_a_topic_that_is_offered_has_a_retelling_prompt() -> None:
    assert session_prompt("forged topic") is None


async def test_a_newline_counts_once_toward_the_length_limit(
    session: AsyncSession, learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None
    text = "\r\n".join(["a" * 99] * 10)
    llm.answer(Correction(corrected_text=text, errors=[]))

    result = await submit_entry(session, llm, learner.id, None, text, NOW)

    assert result.body == "\n".join(["a" * 99] * 10)


@pytest.mark.parametrize(
    ("length", "accepted"), [(19, False), (20, True), (1_000, True), (1_001, False)]
)
async def test_the_length_limits_are_inclusive(
    session: AsyncSession, learner: Learner, llm: FakeLLM, length: int, accepted: bool
) -> None:
    assert learner.id is not None
    text = "a" * length
    llm.answer(Correction(corrected_text=text, errors=[]))

    if accepted:
        await submit_entry(session, llm, learner.id, None, text, NOW)
    else:
        with pytest.raises(InvalidText):
            await submit_entry(session, llm, learner.id, None, text, NOW)


async def test_the_history_is_the_newest_texts_of_this_learner_only(
    session: AsyncSession, learner: Learner, other_learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None and other_learner.id is not None
    for number in range(HISTORY_SIZE + 2):
        text = f"{TEXT} {number}"
        llm.answer(Correction(corrected_text=text, errors=[]))
        await submit_entry(session, llm, learner.id, None, text, NOW)
    llm.answer(Correction(corrected_text=TEXT, errors=[]))
    await submit_entry(session, llm, other_learner.id, None, TEXT, NOW)

    history = await journal_history(session, learner.id)

    assert [entry.body for entry in history] == [
        f"{TEXT} {number}" for number in range(HISTORY_SIZE + 1, 1, -1)
    ]


async def test_the_error_summary_counts_only_this_learners_errors(
    session: AsyncSession, learner: Learner, other_learner: Learner, llm: FakeLLM
) -> None:
    assert learner.id is not None and other_learner.id is not None
    correction = Correction(
        corrected_text=FIXED,
        errors=[FoundError(original="Yo soy", corrected="Estoy", category="ser_estar", note="n")],
    )
    for learner_id in (learner.id, other_learner.id, other_learner.id):
        llm.answer(correction)
        await submit_entry(session, llm, learner_id, None, TEXT, NOW)

    summary = await error_summary(session, learner.id)

    assert [(c.unit_id, c.count) for c in summary] == [("ser_estar", 1)]


async def test_an_old_entry_naming_a_removed_unit_has_no_lesson_to_link(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    gone = JournalError(ErrorKind.GRAMMAR, "gone_unit", "a", "b", "n")
    await save_journal_entry(session, learner.id, None, TEXT, FIXED, [gone])

    history = await journal_history(session, learner.id)

    assert [error.unit_id for error in history[0].errors] == [None]


async def _save_cards(
    session: AsyncSession, learner: Learner, *lemmas: str
) -> dict[str, dict[KnowledgeType, MemoryCard]]:
    assert learner.id is not None
    lexemes = await get_lexemes_by_lemmas(session, lemmas)
    saved: dict[str, dict[KnowledgeType, MemoryCard]] = {}
    for lexeme in lexemes:
        assert lexeme.id is not None
        cards = await save_word(session, learner.id, lexeme.id, "Una frase.", NOW)
        saved[lexeme.lemma] = {card.knowledge_type: card for card in cards}
    return saved


async def _reviews(session: AsyncSession) -> list[ReviewLog]:
    return list((await session.execute(select(ReviewLog))).scalars())


async def test_a_word_written_right_gets_a_good_review_from_writing(
    session: AsyncSession, learner: Learner, llm: FakeLLM, rank_text: RankFn
) -> None:
    assert learner.id is not None
    await rank_text(TEXT, 100)
    cards = await _save_cards(session, learner, "trabajar")
    recall = cards["trabajar"][KnowledgeType.RECALL]
    assert recall.id is not None
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    await submit_entry(session, llm, learner.id, None, TEXT, NOW)

    logs = await _reviews(session)
    assert [(log.card_id, log.rating, log.source) for log in logs] == [
        (recall.id, Rating.GOOD, ReviewSource.WRITING)
    ]
    assert recall.due > NOW


async def test_a_word_inside_an_error_is_not_reviewed(
    session: AsyncSession, learner: Learner, llm: FakeLLM, rank_text: RankFn
) -> None:
    assert learner.id is not None
    await rank_text(TEXT, 100)
    cards = await _save_cards(session, learner, "ser", "trabajar")
    llm.answer(
        Correction(
            corrected_text=FIXED,
            errors=[
                FoundError(original="Yo soy", corrected="Estoy", category="ser_estar", note="n")
            ],
        )
    )

    await submit_entry(session, llm, learner.id, None, TEXT, NOW)

    reviewed = {log.card_id for log in await _reviews(session)}
    assert reviewed == {cards["trabajar"][KnowledgeType.RECALL].id}


async def test_a_word_without_a_card_gets_no_card(
    session: AsyncSession, learner: Learner, llm: FakeLLM, rank_text: RankFn
) -> None:
    assert learner.id is not None
    await rank_text(TEXT, 100)
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    await submit_entry(session, llm, learner.id, None, TEXT, NOW)

    assert (await session.execute(select(MemoryCard))).scalars().all() == []
    assert await _reviews(session) == []


async def test_the_recognition_card_of_a_written_word_is_not_reviewed(
    session: AsyncSession, learner: Learner, llm: FakeLLM, rank_text: RankFn
) -> None:
    assert learner.id is not None
    await rank_text(TEXT, 100)
    cards = await _save_cards(session, learner, "trabajar")
    recognize = cards["trabajar"][KnowledgeType.RECOGNIZE]
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    await submit_entry(session, llm, learner.id, None, TEXT, NOW)

    assert recognize.id not in {log.card_id for log in await _reviews(session)}


async def test_a_card_that_is_not_due_is_left_alone(
    session: AsyncSession, learner: Learner, llm: FakeLLM, rank_text: RankFn
) -> None:
    assert learner.id is not None
    await rank_text(TEXT, 100)
    cards = await _save_cards(session, learner, "trabajar")
    recall = cards["trabajar"][KnowledgeType.RECALL]
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    await submit_entry(session, llm, learner.id, None, TEXT, NOW - timedelta(days=1))

    assert await _reviews(session) == []
    assert recall.due == NOW


async def test_a_word_written_twice_is_reviewed_once(
    session: AsyncSession, learner: Learner, llm: FakeLLM, rank_text: RankFn
) -> None:
    assert learner.id is not None
    text = "Trabajo mucho y trabajo los sábados, porque trabajo en una tienda."
    await rank_text(text, 100)
    await _save_cards(session, learner, "trabajar")
    llm.answer(Correction(corrected_text=text, errors=[]))

    await submit_entry(session, llm, learner.id, None, text, NOW)

    assert len(await _reviews(session)) == 1


async def test_the_entry_is_committed_even_when_no_card_is_reviewed(
    session: AsyncSession, learner: Learner, llm: FakeLLM, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert learner.id is not None
    commits: list[int] = []
    commit = session.commit

    async def counting_commit() -> None:
        commits.append(1)
        await commit()

    monkeypatch.setattr(session, "commit", counting_commit)
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    await submit_entry(session, llm, learner.id, None, TEXT, NOW)

    assert commits == [1]
