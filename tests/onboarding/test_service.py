from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from soltura.learner.models import (
    Learner,
    LearnerLexeme,
    Lexeme,
    LexemeOrigin,
    LexemeStatus,
)
from soltura.onboarding.service import (
    PlacementItem,
    PlacementSentence,
    PlacementSentences,
    apply_placement,
    build_placement,
    score_placement,
)
from tests.onboarding.conftest import CORRECT, JudgeByAnswer


def _sentences_for(lemmas: list[str]) -> PlacementSentences:
    return PlacementSentences(
        sentences=[
            PlacementSentence(lemma=lemma, sentence=f"Hoy veo {lemma} en casa.", target_form=lemma)
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


async def test_placement_asks_five_content_words_from_every_band(
    session: AsyncSession, banded_lexemes: list[Lexeme], judge: JudgeByAnswer
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    judge.answer(_sentences_for(nouns))

    items = await build_placement(session, judge)

    assert len(items) == 40
    assert {item.band: sum(i.band == item.band for i in items) for item in items} == {
        band: 5 for band in range(8)
    }
    assert not any(item.lemma.startswith("prep") for item in items)
    assert len(judge.prompts) == 1


async def test_a_word_without_a_usable_sentence_is_left_out(
    session: AsyncSession, banded_lexemes: list[Lexeme], judge: JudgeByAnswer
) -> None:
    nouns = [lexeme.lemma for lexeme in banded_lexemes if lexeme.pos == "NOUN"]
    sentences = _sentences_for(nouns[1:])
    sentences.sentences.append(
        PlacementSentence(lemma=nouns[0], sentence="Una frase sin la palabra.", target_form="x")
    )
    judge.answer(sentences)

    items = await build_placement(session, judge)

    assert len(items) == 39
    assert nouns[0] not in {item.lemma for item in items}


async def test_all_right_answers_place_the_learner_at_the_last_band(judge: JudgeByAnswer) -> None:
    result = await score_placement(judge, _answered([5] * 8))

    assert result.known_rank == 6000


async def test_all_wrong_answers_place_the_learner_nowhere(judge: JudgeByAnswer) -> None:
    result = await score_placement(judge, _answered([0] * 8))

    assert result.known_rank == 0


async def test_only_an_unbroken_run_of_passed_bands_counts(judge: JudgeByAnswer) -> None:
    # 5/5, 4/5 pass; 3/5 fails, so the later 5/5 bands do not count.
    result = await score_placement(judge, _answered([5, 4, 3, 5, 5, 5, 5, 5]))

    assert result.known_rank == 500
    assert [(band.correct, band.total) for band in result.bands[:3]] == [(5, 5), (4, 5), (3, 5)]


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

    await apply_placement(session, learner.id, known_rank=500)

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

    await apply_placement(session, learner.id, known_rank=0)

    assert (await session.execute(select(LearnerLexeme))).scalars().all() == []
