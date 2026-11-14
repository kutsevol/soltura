import importlib
import pkgutil
from functools import cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from soltura.grammar import content

SEPARATOR = "|"
GAP = "___"

Level = Literal["A1", "A2", "B1"]


class Example(BaseModel):
    model_config = ConfigDict(frozen=True)

    spanish: str = Field(description="A Spanish sentence that shows the rule")
    ukrainian: str = Field(description="Its Ukrainian translation")


class Lesson(BaseModel):
    model_config = ConfigDict(frozen=True)

    points: tuple[str, ...] = Field(description="The rule in Ukrainian, one short point each")
    examples: tuple[Example, ...] = Field(description="Sentences that show the rule at work")


class Exercise(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Stable id inside the unit; part of the card key")
    sentence: str = Field(description="Spanish sentence with the word to fill in marked as ___")
    translation: str = Field(description="Ukrainian translation of the whole sentence")
    options: tuple[str, ...] = Field(
        description="Two or three options to choose from; empty when the learner types the word"
    )
    answer: str = Field(description="The word that fills the gap")
    note: str = Field(description="One line in Ukrainian saying why this is the answer")

    @property
    def is_choice(self) -> bool:
        return bool(self.options)


class GrammarUnit(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(description="Stable id of the unit; cards and the error log refer to it")
    level: Level = Field(description="CEFR level the unit is taught at")
    order: int = Field(description="Teaching order inside the level, spaced by 10")
    title: str = Field(description="Title of the lesson in Ukrainian")
    lesson: Lesson = Field(description="The rule and its examples")
    exercises: tuple[Exercise, ...] = Field(description="Exercises scheduled when the unit starts")


@cache
def all_units() -> tuple[GrammarUnit, ...]:
    units = [
        importlib.import_module(f"{content.__name__}.{module.name}").UNIT
        for module in pkgutil.iter_modules(content.__path__)
    ]
    return tuple(sorted(units, key=lambda unit: (unit.level, unit.order)))


def get_unit(unit_id: str) -> GrammarUnit | None:
    return next((unit for unit in all_units() if unit.id == unit_id), None)


def next_unit(started_ids: set[str]) -> GrammarUnit | None:
    return next((unit for unit in all_units() if unit.id not in started_ids), None)


def exercise_key(unit_id: str, exercise_id: str) -> str:
    return SEPARATOR.join((unit_id, exercise_id))


def unit_keys(unit: GrammarUnit) -> list[str]:
    return [exercise_key(unit.id, exercise.id) for exercise in unit.exercises]


def parse_exercise_key(key: str | None) -> tuple[GrammarUnit, Exercise] | None:
    parts = (key or "").split(SEPARATOR)
    if len(parts) != 2:
        return None
    unit = get_unit(parts[0])
    if unit is None:
        return None
    exercise = next((exercise for exercise in unit.exercises if exercise.id == parts[1]), None)
    return (unit, exercise) if exercise is not None else None


def started_unit_ids(keys: set[str]) -> set[str]:
    return {key.split(SEPARATOR)[0] for key in keys}
