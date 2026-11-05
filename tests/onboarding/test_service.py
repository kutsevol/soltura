from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from soltura.learner.models import (
    Learner,
    LearnerLexeme,
    Lexeme,
    LexemeOrigin,
    LexemeStatus,
    MemoryCard,
    WordContext,
)
from soltura.learner.repository import save_placement_run
from soltura.onboarding.service import (
    LEARN_BATCH,
    BandScore,
    Finished,
    MissedSummary,
    NextWord,
    NothingToAnswer,
    PlacementItem,
    PlacementResult,
    PlacementSentence,
    PlacementSentences,
    WordResult,
    answer_word,
    apply_placement,
    build_placement,
    get_latest_placement,
    learn_from_result,
    learn_missed_words,
    missed_summary,
    missed_words,
    score_placement,
    should_stop,
)
from tests.factories import LexemeFactory
from tests.onboarding.conftest import CORRECT, JudgeByAnswer

NOW = datetime(2026, 10, 31, 12, 0, tzinfo=UTC)


def _sentences_for(lemmas: list[str]) -> PlacementSentences:
    return PlacementSentences(
        sentences=[
            PlacementSentence(
                lemma=lemma,
                sentence=f"Hoy veo {lemma} en casa.",
                target_form=lemma,
                meaning=f"значення {lemma}",
            )
            for lemma in lemmas
        ]
    )


def _answered(correct_per_band: list[int]) -> list[PlacementItem]:
    return [
        PlacementItem(
            band=band,
            lemma=f"word{band}x{i}",
            sentence=f"Hoy veo word{band}x{i}.",
            target_form=f"word{band}x{i}",
            answer=CORRECT if i < correct else "ні",
        )
        for band, correct in enumerate(correct_per_band)
        for i in range(5)
    ]


async def test_placement_asks_eight_content_words_from_every_band(
    session: AsyncSession, banded_lexemes: list[Lexeme], judge: JudgeByAnswer
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    judge.answer(_sentences_for(nouns))

    items = await build_placement(session, judge)

    assert len(items) == 64
    assert {item.band: sum(i.band == item.band for i in items) for item in items} == {
        band: 8 for band in range(8)
    }
    assert not any(item.lemma.startswith("prep") for item in items)
    assert len(judge.prompts) == 1


async def test_a_word_without_a_usable_sentence_is_left_out(
    session: AsyncSession, banded_lexemes: list[Lexeme], judge: JudgeByAnswer
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    sentences = _sentences_for(nouns[1:])
    sentences.sentences.append(
        PlacementSentence(
            lemma=nouns[0], sentence="Una frase sin la palabra.", target_form="x", meaning="x"
        )
    )
    judge.answer(sentences)

    items = await build_placement(session, judge)

    assert len(items) == 64
    assert nouns[0] not in {item.lemma for item in items}


async def test_an_unusable_word_is_left_out_and_a_spare_word_takes_its_place(
    session: AsyncSession, banded_lexemes: list[Lexeme], judge: JudgeByAnswer
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    sentences = _sentences_for(nouns)
    sentences.sentences[0].is_usable = False
    judge.answer(sentences)

    items = await build_placement(session, judge)

    assert nouns[0] not in {item.lemma for item in items}
    assert sum(item.band == 0 for item in items) == 8


async def test_all_right_answers_place_the_learner_at_the_last_band(judge: JudgeByAnswer) -> None:
    result = await score_placement(judge, _answered([5] * 8))

    assert result.known_rank == 6000


async def test_all_wrong_answers_place_the_learner_nowhere(judge: JudgeByAnswer) -> None:
    result = await score_placement(judge, _answered([0] * 8))

    assert result.known_rank == 0


async def test_only_an_unbroken_run_of_passed_bands_counts(judge: JudgeByAnswer) -> None:
    # 5/5, 3/5 pass at 60%; 2/5 fails, so the later 5/5 bands do not count.
    result = await score_placement(judge, _answered([5, 3, 2, 5, 5, 5, 5, 5]))

    assert result.known_rank == 500
    assert [(band.correct, band.total) for band in result.bands[:3]] == [(5, 5), (3, 5), (2, 5)]


async def test_applying_a_placement_marks_frequent_words_known_but_keeps_learning_ones(
    session: AsyncSession, learner: Learner, banded_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    being_learned = next(lexeme for lexeme in banded_lexemes if lexeme.frequency_rank == 250)
    assert being_learned.id is not None
    session.add(
        LearnerLexeme(
            learner_id=learner.id,
            lexeme_id=being_learned.id,
            status=LexemeStatus.LEARNING,
            origin=LexemeOrigin.READING,
        )
    )
    await session.flush()

    await apply_placement(session, learner.id, PlacementResult(known_rank=500, bands=[]))

    statuses = dict(
        (
            await session.execute(
                select(LearnerLexeme.status, func.count())
                .where(col(LearnerLexeme.learner_id) == learner.id)
                .group_by(col(LearnerLexeme.status))
            )
        ).all()
    )
    expected_known = sum(1 for lexeme in banded_lexemes if lexeme.frequency_rank <= 500) - 1
    assert statuses == {LexemeStatus.KNOWN: expected_known, LexemeStatus.LEARNING: 1}


async def test_a_placement_with_no_passed_band_marks_nothing(
    session: AsyncSession, learner: Learner, banded_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None

    await apply_placement(session, learner.id, PlacementResult(known_rank=0, bands=[]))

    assert (await session.execute(select(LearnerLexeme))).scalars().all() == []


async def test_a_placement_run_is_kept_even_when_no_band_passed(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    result = PlacementResult(
        known_rank=0, bands=[BandScore(band=0, max_rank=250, correct=1, total=5)]
    )

    await apply_placement(session, learner.id, result)

    assert await get_latest_placement(session, learner.id) == result


async def test_the_latest_placement_is_the_newest_run(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    older = PlacementResult(known_rank=250, bands=[BandScore(0, 250, 4, 5)])
    newer = PlacementResult(
        known_rank=500, bands=[BandScore(0, 250, 5, 5), BandScore(1, 500, 4, 5)]
    )

    await apply_placement(session, learner.id, older)
    await apply_placement(session, learner.id, newer)

    assert await get_latest_placement(session, learner.id) == newer


async def test_there_is_no_placement_before_the_first_run(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    assert await get_latest_placement(session, learner.id) is None


async def test_every_answer_is_kept_with_its_verdict_and_expected_meaning(
    judge: JudgeByAnswer,
) -> None:
    result = await score_placement(judge, _answered([3] + [0] * 7))

    first_band = result.words[:5]
    assert [word.verdict for word in first_band] == ["correct"] * 3 + ["wrong"] * 2
    assert (first_band[0].lemma, first_band[0].answer) == ("word0x0", CORRECT)
    assert (first_band[4].answer, first_band[4].expected) == ("ні", "значення")
    assert len(result.words) == 40


async def test_the_saved_answers_come_back_with_the_latest_placement(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer
) -> None:
    assert learner.id is not None
    result = await score_placement(judge, _answered([5, 2] + [0] * 6))

    await apply_placement(session, learner.id, result)

    assert await get_latest_placement(session, learner.id) == result


async def test_a_run_saved_before_answers_were_kept_has_no_words(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    bands = [{"band": 0, "max_rank": 250, "correct": 5, "total": 5}]
    await save_placement_run(session, learner.id, 250, bands)

    result = await get_latest_placement(session, learner.id)

    assert result is not None
    assert (result.known_rank, result.words) == (250, [])


async def test_a_skipped_word_keeps_the_meaning_written_with_its_sentence(
    judge: JudgeByAnswer,
) -> None:
    skipped = PlacementItem(
        band=0, lemma="casa", sentence="Mi casa es pequeña.", target_form="casa", meaning="дім"
    )

    result = await score_placement(judge, [skipped])

    [word] = result.words
    assert (word.verdict, word.answer, word.expected) == ("wrong", "", "дім")
    assert judge.prompts == []


async def test_the_meaning_of_each_placement_word_comes_from_its_sentence(
    session: AsyncSession, banded_lexemes: list[Lexeme], judge: JudgeByAnswer
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    judge.answer(_sentences_for(nouns))

    items = await build_placement(session, judge)

    assert all(item.meaning == f"значення {item.lemma}" for item in items)


def test_two_weak_bands_in_a_row_stop_the_test() -> None:
    scores = [BandScore(0, 250, 8, 8), BandScore(1, 500, 3, 8), BandScore(2, 1000, 2, 8)]

    assert should_stop(scores)


def test_one_weak_band_or_a_weak_band_between_strong_ones_does_not_stop_the_test() -> None:
    assert not should_stop([BandScore(0, 250, 8, 8), BandScore(1, 500, 3, 8)])
    assert not should_stop(
        [BandScore(0, 250, 3, 8), BandScore(1, 500, 7, 8), BandScore(2, 1000, 3, 8)]
    )


def test_a_band_at_exactly_half_is_weak() -> None:
    assert should_stop([BandScore(0, 250, 4, 8), BandScore(1, 500, 4, 8)])


def test_a_band_just_over_half_is_not_weak() -> None:
    assert not should_stop([BandScore(0, 250, 5, 8), BandScore(1, 500, 5, 8)])


async def test_only_the_bands_that_were_asked_are_scored(judge: JudgeByAnswer) -> None:
    result = await score_placement(judge, _answered([5, 5]))

    assert [band.max_rank for band in result.bands] == [250, 500]


async def test_an_answer_that_is_already_judged_is_not_judged_again(
    judge: JudgeByAnswer,
) -> None:
    judged = _answered([5])[0].model_copy(
        update={"verdict": "correct", "reason": "", "expected": "значення"}
    )

    result = await score_placement(judge, [judged])

    assert judge.prompts == []
    assert result.words[0].verdict == "correct"


async def test_a_word_shown_in_two_bands_under_different_case_is_asked_once(
    session: AsyncSession, judge: JudgeByAnswer
) -> None:
    session.add_all(
        [
            LexemeFactory.build(lemma="claro", pos="ADJ", frequency_rank=10),
            LexemeFactory.build(lemma="claridad", pos="NOUN", frequency_rank=5000),
        ]
    )
    await session.flush()
    judge.answer(
        PlacementSentences(
            sentences=[
                PlacementSentence(
                    lemma="claro", sentence="Claro que sí.", target_form="Claro", meaning="звісно"
                ),
                PlacementSentence(
                    lemma="claridad",
                    sentence="Hay un claro en el cielo.",
                    target_form="claro",
                    meaning="просвіт",
                ),
            ]
        )
    )

    items = await build_placement(session, judge)

    assert [(item.band, item.target_form) for item in items] == [(0, "Claro")]


def _word(lemma: str, verdict: str) -> WordResult:
    return WordResult(
        band=0,
        lemma=lemma,
        sentence=f"Hoy veo {lemma}.",
        target_form=lemma,
        answer="",
        verdict=verdict,
        reason="",
        expected="значення",
    )


async def test_a_word_answered_right_is_known_even_above_the_known_rank(
    session: AsyncSession, learner: Learner, banded_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    result = PlacementResult(known_rank=0, bands=[], words=[_word("word5x0", "correct")])

    await apply_placement(session, learner.id, result)

    known = (
        await session.execute(
            select(Lexeme.lemma)
            .join(LearnerLexeme, col(LearnerLexeme.lexeme_id) == col(Lexeme.id))
            .where(col(LearnerLexeme.learner_id) == learner.id)
        )
    ).scalars()
    assert list(known) == ["word5x0"]


async def test_missed_words_skip_right_answers_and_words_being_learned_most_frequent_first(
    session: AsyncSession, learner: Learner, banded_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    by_lemma = {lexeme.lemma: lexeme for lexeme in banded_lexemes}
    being_learned = by_lemma["word2x0"]
    assert being_learned.id is not None
    session.add(
        LearnerLexeme(
            learner_id=learner.id,
            lexeme_id=being_learned.id,
            status=LexemeStatus.LEARNING,
            origin=LexemeOrigin.READING,
        )
    )
    words = [
        _word("word5x0", "wrong"),
        _word("word0x0", "wrong"),
        _word("word1x0", "correct"),
        _word("word3x0", "partly"),
        _word("word2x0", "wrong"),
    ]
    await apply_placement(session, learner.id, PlacementResult(known_rank=0, bands=[], words=words))

    missed = await missed_words(session, learner.id)

    assert [word.lemma for word in missed] == ["word0x0", "word3x0", "word5x0"]


async def test_one_press_adds_a_batch_with_cards_and_sentences_and_the_next_press_the_rest(
    session: AsyncSession, learner: Learner, banded_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    lemmas = [f"word{band}x{i}" for band in range(4) for i in range(5)]
    words = [_word(lemma, "wrong") for lemma in lemmas]
    await apply_placement(session, learner.id, PlacementResult(known_rank=0, bands=[], words=words))

    first = await learn_missed_words(session, learner.id, NOW)
    second = await learn_missed_words(session, learner.id, NOW)
    third = await learn_missed_words(session, learner.id, NOW)

    assert first == (LEARN_BATCH, 5)
    assert second == (5, 0)
    assert third == (0, 0)
    cards = (await session.execute(select(func.count()).select_from(MemoryCard))).scalar_one()
    contexts = (await session.execute(select(WordContext.sentence))).scalars().all()
    assert cards == 40
    assert sorted(contexts) == sorted(f"Hoy veo {lemma}." for lemma in lemmas)


def _items(band: int, count: int, answer: str = "") -> list[PlacementItem]:
    return [
        PlacementItem(
            band=band,
            lemma=f"word{band}x{i}",
            sentence=f"Hoy veo word{band}x{i}.",
            target_form=f"word{band}x{i}",
            answer=answer,
        )
        for i in range(count)
    ]


async def test_answering_inside_a_band_only_records_the_answer(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer
) -> None:
    assert learner.id is not None

    step = await answer_word(session, judge, learner.id, _items(0, 3), [], " hola ", False)

    assert isinstance(step, NextWord)
    assert [item.lemma for item in step.queue] == ["word0x1", "word0x2"]
    assert [item.answer for item in step.answered] == ["hola"]
    assert judge.prompts == []


async def test_giving_up_records_an_empty_answer(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer
) -> None:
    assert learner.id is not None

    step = await answer_word(session, judge, learner.id, _items(0, 2), [], "texto", True)

    assert isinstance(step, NextWord)
    assert step.answered[0].answer == ""


async def test_the_last_word_of_a_band_judges_the_band_once(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer
) -> None:
    assert learner.id is not None
    queue = _items(0, 1) + _items(1, 2)

    boundary = await answer_word(session, judge, learner.id, queue, [], CORRECT, False)

    assert isinstance(boundary, NextWord)
    assert [item.verdict for item in boundary.answered] == ["correct"]
    assert len(judge.prompts) == 1
    inside = await answer_word(
        session, judge, learner.id, boundary.queue, boundary.answered, "x", False
    )
    assert isinstance(inside, NextWord)
    assert len(judge.prompts) == 1


async def test_two_weak_bands_in_a_row_finish_the_test_and_save_the_run(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer
) -> None:
    assert learner.id is not None
    answered = _items(0, 2, "ні") + _items(1, 1, "ні")
    queue = _items(1, 1) + _items(2, 2)

    step = await answer_word(session, judge, learner.id, queue, answered, "ні", False)

    assert isinstance(step, Finished)
    assert [band.max_rank for band in step.result.bands] == [250, 500]
    assert await get_latest_placement(session, learner.id) == step.result


async def test_the_last_word_of_the_queue_finishes_the_test(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer
) -> None:
    assert learner.id is not None

    step = await answer_word(session, judge, learner.id, _items(0, 1), [], CORRECT, False)

    assert isinstance(step, Finished)
    assert step.result.known_rank == 250


async def test_answering_with_an_empty_queue_is_refused(
    session: AsyncSession, learner: Learner, judge: JudgeByAnswer
) -> None:
    assert learner.id is not None

    with pytest.raises(NothingToAnswer):
        await answer_word(session, judge, learner.id, [], [], "x", False)


async def test_a_learner_without_a_run_has_nothing_missed(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    assert await missed_summary(session, learner.id) == MissedSummary(total=0, batch=0)


async def test_learning_from_the_result_reports_what_was_added_and_what_is_left(
    session: AsyncSession, learner: Learner, banded_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    words = [_word(f"word{band}x{i}", "wrong") for band in range(4) for i in range(5)]
    await apply_placement(session, learner.id, PlacementResult(known_rank=0, bands=[], words=words))

    outcome = await learn_from_result(session, learner.id, NOW)

    assert outcome.added == LEARN_BATCH
    assert outcome.missed == MissedSummary(total=5, batch=5)
