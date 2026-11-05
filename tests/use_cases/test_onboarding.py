from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner, Lexeme
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
    apply_placement,
    get_latest_placement,
)
from soltura.use_cases.onboarding import (
    answer_word,
    build_placement,
    latest_result_screen,
    learn_from_result,
    result_screen,
)
from tests.conftest import CORRECT, JudgeByAnswer
from tests.factories import LexemeFactory
from tests.fakes import placement_word

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


async def test_the_meaning_of_each_placement_word_comes_from_its_sentence(
    session: AsyncSession, banded_lexemes: list[Lexeme], judge: JudgeByAnswer
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    judge.answer(_sentences_for(nouns))

    items = await build_placement(session, judge)

    assert all(item.meaning == f"значення {item.lemma}" for item in items)


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


async def test_learning_from_the_result_reports_what_was_added_and_what_is_left(
    session: AsyncSession, learner: Learner, banded_lexemes: list[Lexeme]
) -> None:
    assert learner.id is not None
    words = [placement_word(f"word{band}x{i}", "wrong") for band in range(4) for i in range(5)]
    await apply_placement(session, learner.id, PlacementResult(known_rank=0, bands=[], words=words))

    outcome = await learn_from_result(session, learner.id, NOW)

    assert outcome.added == LEARN_BATCH
    assert outcome.missed == MissedSummary(total=5, batch=5)


async def test_a_learner_without_a_run_has_no_result_screen(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None

    assert await latest_result_screen(session, learner.id) is None


async def test_the_result_screen_carries_the_reading_range_of_the_saved_run(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    result = PlacementResult(known_rank=1000, bands=[BandScore(0, 250, 8, 8)])
    await apply_placement(session, learner.id, result)

    screen = await result_screen(session, learner.id, result)

    assert screen.result == result
    assert screen.reading_range == 1000
    assert screen.missed.total == 0


async def test_a_run_that_passed_no_band_still_reads_at_the_first_band(
    session: AsyncSession, learner: Learner
) -> None:
    assert learner.id is not None
    result = PlacementResult(known_rank=0, bands=[BandScore(0, 250, 2, 8)])
    await apply_placement(session, learner.id, result)

    screen = await latest_result_screen(session, learner.id)

    assert screen is not None
    assert screen.reading_range == 250
