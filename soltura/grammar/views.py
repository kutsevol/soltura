import random
from dataclasses import dataclass
from datetime import datetime

from soltura.grammar.service import ExerciseResult, GrammarItem, GrammarProgress, UnitProgress
from soltura.grammar.units import GAP, Example, GrammarUnit, get_unit
from soltura.practice.checking import SpanishCheck
from soltura.practice.views import RATING_LABEL

LEVEL_LABEL = {"A2": "Рівень A2", "B1": "Рівень B1"}


@dataclass(frozen=True)
class LessonView:
    unit_id: str
    title: str
    level: str
    points: tuple[str, ...]
    examples: tuple[Example, ...]


@dataclass(frozen=True)
class CardView:
    card_id: int
    title: str
    before: str
    after: str
    translation: str
    options: tuple[str, ...]
    remaining: int


@dataclass(frozen=True)
class ResultView:
    label: str
    tone: str
    answer: str
    explanation: str
    expected: str
    note: str
    lesson_href: str


def lesson_view(unit: GrammarUnit) -> LessonView:
    return LessonView(
        unit_id=unit.id,
        title=unit.title,
        level=LEVEL_LABEL[unit.level],
        points=unit.lesson.points,
        examples=unit.lesson.examples,
    )


def card_view(item: GrammarItem, remaining: int) -> CardView:
    unit = get_unit(item.unit_id)
    assert unit is not None
    exercise = next(exercise for exercise in unit.exercises if exercise.id == item.exercise_id)
    before, _, after = exercise.sentence.partition(GAP)
    # The order is fixed per card, so a reload shows the same buttons, and it differs
    # between cards, so the right option is not always in the same place.
    options = tuple(random.Random(item.card_id).sample(exercise.options, len(exercise.options)))
    return CardView(
        card_id=item.card_id,
        title=unit.title,
        before=before,
        after=after,
        translation=exercise.translation,
        options=options,
        remaining=remaining,
    )


def _explanation(check: SpanishCheck) -> str:
    return {
        SpanishCheck.EXACT: "Правильно.",
        SpanishCheck.ACCENT_SLIP: "Майже: перевірте наголос.",
    }.get(check, "Це не те слово.")


def result_view(result: ExerciseResult, answer: str) -> ResultView:
    return ResultView(
        label=RATING_LABEL[result.rating],
        tone=result.rating.value,
        answer=answer.strip(),
        explanation=_explanation(result.check),
        expected=result.expected,
        note=result.note,
        lesson_href=f"/grammar/units/{result.unit_id}",
    )


@dataclass(frozen=True)
class ProgressRow:
    unit_id: str
    title: str
    level: str
    answers_text: str
    memory_text: str
    due_text: str


@dataclass(frozen=True)
class ProgressView:
    rows: list[ProgressRow]
    not_started: int


def _progress_row(progress: UnitProgress, now: datetime) -> ProgressRow:
    unit = progress.unit
    if progress.answers:
        answers_text = (
            f"Відповідей: {progress.answers}, правильних: "
            f"{round(100 * progress.right / progress.answers)}%"
        )
    else:
        answers_text = "Ще без відповідей"
    due_text = (
        "Є що повторити"
        if progress.next_due <= now
        else f"Наступне повторення: {progress.next_due:%d.%m}"
    )
    return ProgressRow(
        unit_id=unit.id,
        title=unit.title,
        level=LEVEL_LABEL[unit.level],
        answers_text=answers_text,
        memory_text=f"У пам’яті: {progress.solid} з {len(unit.exercises)}",
        due_text=due_text,
    )


def progress_view(progress: GrammarProgress, now: datetime) -> ProgressView:
    return ProgressView(
        rows=[_progress_row(unit, now) for unit in progress.units],
        not_started=progress.not_started,
    )
