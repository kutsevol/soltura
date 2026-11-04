from sqlalchemy.ext.asyncio import AsyncSession

from soltura.learner.models import Learner, Lexeme
from soltura.onboarding.service import BANDS, PlacementResult, apply_placement
from soltura.words.vocabulary import EDGES, build_vocabulary_map


async def test_the_map_runs_through_the_placement_bands_and_two_more(
    session: AsyncSession, learner: Learner, vocabulary_words: None
) -> None:
    assert learner.id is not None

    vocabulary = await build_vocabulary_map(session, learner.id)

    assert [(band.min_rank, band.max_rank) for band in vocabulary.bands[: len(BANDS)]] == list(
        BANDS
    )
    assert [(band.min_rank, band.max_rank) for band in vocabulary.bands] == list(EDGES)
    assert len(vocabulary.bands) == len(BANDS) + 2


async def test_a_saved_word_is_learning_and_names_and_unranked_words_are_left_out(
    session: AsyncSession, learner: Learner, vocabulary_words: None
) -> None:
    assert learner.id is not None

    vocabulary = await build_vocabulary_map(session, learner.id)

    first, second = vocabulary.bands[:2]
    assert (first.total, first.known, first.learning) == (3, 1, 1)
    assert (second.total, second.known, second.learning) == (1, 1, 0)
    assert vocabulary.bands[-1].total == 1
    assert (vocabulary.total, vocabulary.known) == (5, 2)


async def test_a_placement_result_fills_the_bands_up_to_its_rank(
    session: AsyncSession, learner: Learner, vocabulary_lexemes: dict[str, Lexeme]
) -> None:
    assert learner.id is not None
    await apply_placement(session, learner.id, PlacementResult(known_rank=500, bands=[]))

    vocabulary = await build_vocabulary_map(session, learner.id)

    first, second, *rest = vocabulary.bands
    assert (first.known, first.total) == (3, 3)
    assert (second.known, second.total) == (1, 1)
    assert all(band.known == 0 for band in rest)


async def test_a_learner_without_words_has_empty_bars(
    session: AsyncSession, learner: Learner, vocabulary_lexemes: dict[str, Lexeme]
) -> None:
    assert learner.id is not None

    vocabulary = await build_vocabulary_map(session, learner.id)

    assert vocabulary.known == 0
    assert vocabulary.total == 5
    assert all(band.known == 0 and band.learning == 0 for band in vocabulary.bands)
