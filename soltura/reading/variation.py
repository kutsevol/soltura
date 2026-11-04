import random
from collections.abc import Sequence
from dataclasses import dataclass

FORMS = (
    "a conversation between two people",
    "a short message one person writes to another",
    "a notice or announcement posted in a public place",
    "a short story told by the narrator",
    "a diary entry",
)

NAMES = (
    "Lucía",
    "Javier",
    "Carmen",
    "Pablo",
    "Elena",
    "Mateo",
    "Sofía",
    "Andrés",
    "Irene",
    "Diego",
    "Rosa",
    "Tomás",
)


@dataclass(frozen=True)
class Variation:
    situation: str | None
    form: str
    name: str


def pick_variation(situations: Sequence[str], rng: random.Random) -> Variation:
    return Variation(
        situation=rng.choice(situations) if situations else None,
        form=rng.choice(FORMS),
        name=rng.choice(NAMES),
    )


def variation_prompt(variation: Variation, recent_titles: Sequence[str]) -> str:
    parts = []
    if variation.situation:
        parts.append(f"Situation: {variation.situation}.")
    parts.append(f"Write it as {variation.form}. If a person is named, call them {variation.name}.")
    if recent_titles:
        parts.append(f"Do not repeat these recent texts: {'; '.join(recent_titles)}.")
    return " " + " ".join(parts)
