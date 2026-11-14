import random

import pytest

from soltura.reading.service import new_word_count, pick_new_words


@pytest.mark.parametrize(("vocabulary", "count"), [(250, 1), (251, 3), (3000, 3)])
def test_only_the_first_band_plans_a_single_new_word(vocabulary: int, count: int) -> None:
    assert new_word_count(vocabulary) == count


def test_the_same_seed_draws_the_same_words_in_any_order() -> None:
    candidates = ["casa", "perro", "mesa", "libro", "calle"]

    first = pick_new_words(candidates, 1000, random.Random(7))
    second = pick_new_words(list(reversed(candidates)), 1000, random.Random(7))

    assert first == second
    assert len(set(first)) == 3


def test_fewer_candidates_than_the_count_are_all_drawn() -> None:
    assert sorted(pick_new_words(["casa", "perro"], 1000, random.Random(1))) == ["casa", "perro"]
    assert pick_new_words([], 1000, random.Random(1)) == []
