import random

from soltura.reading.variation import Variation, pick_variation, variation_prompt

SITUATIONS = ("a leak", "a deposit", "a flatmate")


def test_the_same_seed_picks_the_same_variation() -> None:
    first = pick_variation(SITUATIONS, random.Random(7))
    second = pick_variation(SITUATIONS, random.Random(7))

    assert first == second


def test_different_seeds_give_different_variations() -> None:
    picks = {pick_variation(SITUATIONS, random.Random(seed)) for seed in range(20)}

    assert len(picks) > 5


def test_a_topic_without_situations_picks_only_a_form_and_a_name() -> None:
    picked = pick_variation((), random.Random(1))

    assert picked.situation is None
    assert "Situation:" not in variation_prompt(picked, [])


def test_the_prompt_lists_the_recent_titles_to_avoid() -> None:
    prompt = variation_prompt(Variation("a leak", "a diary entry", "Rosa"), ["Un día", "La cola"])

    assert "Situation: a leak." in prompt
    assert "a diary entry" in prompt
    assert "call them Rosa" in prompt
    assert "Do not repeat these recent texts: Un día; La cola." in prompt
