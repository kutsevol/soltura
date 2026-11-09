from dataclasses import dataclass

from soltura.learner.models import ErrorKind
from soltura.use_cases.writing import JournalResult
from soltura.writing.service import (
    MAX_LENGTH,
    MIN_LENGTH,
    SUGGEST_AFTER,
    ErrorCategory,
    Segment,
    TextProblem,
)

KIND_LABEL = {
    ErrorKind.GRAMMAR: "Граматика",
    ErrorKind.VOCABULARY: "Слово",
    ErrorKind.SPELLING: "Правопис",
    ErrorKind.OTHER: "Інше",
}

FREE_TOPIC = "Вільна тема"

PROBLEM_MESSAGE = {
    TextProblem.TOO_SHORT: f"Напишіть хоча б кілька речень: від {MIN_LENGTH} символів.",
    TextProblem.TOO_LONG: f"Текст задовгий: не більше {MAX_LENGTH} символів.",
}


def lesson_href(unit_id: str | None) -> str | None:
    return f"/grammar/units/{unit_id}" if unit_id else None


@dataclass(frozen=True)
class ErrorView:
    kind: str
    original: str
    corrected: str
    note: str
    lesson_href: str | None


@dataclass(frozen=True)
class EntryView:
    prompt: str
    date: str
    summary: str
    segments: list[Segment]
    errors: list[ErrorView]


def entry_view(result: JournalResult) -> EntryView:
    count = len(result.errors)
    return EntryView(
        prompt=result.prompt or FREE_TOPIC,
        date=result.created_at.strftime("%d.%m.%Y"),
        summary=f"Знайдено помилок: {count}" if count else "Помилок не знайдено",
        segments=result.segments,
        errors=[
            ErrorView(
                KIND_LABEL[error.kind],
                error.original,
                error.corrected,
                error.note,
                lesson_href(error.unit_id),
            )
            for error in result.errors
        ],
    )


@dataclass(frozen=True)
class CategoryView:
    label: str
    count: int
    original: str
    corrected: str
    lesson_href: str | None
    suggestion: str | None


def category_view(category: ErrorCategory) -> CategoryView:
    return CategoryView(
        label=category.title or KIND_LABEL[category.kind],
        count=category.count,
        original=category.last.original,
        corrected=category.last.corrected or "—",
        lesson_href=lesson_href(category.unit_id),
        suggestion=(
            f"Помилок у цьому правилі: {SUGGEST_AFTER} і більше. Варто перечитати урок."
            if category.suggested
            else None
        ),
    )
