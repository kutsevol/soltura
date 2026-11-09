from datetime import UTC, datetime

from soltura.learner.models import ErrorKind
from soltura.learner.repository import JournalError
from soltura.use_cases.writing import JournalResult
from soltura.writing.service import Segment, SegmentKind
from soltura.writing.views import FREE_TOPIC, entry_view


def _result(prompt: str | None, errors: list[JournalError]) -> JournalResult:
    return JournalResult(
        entry_id=1,
        prompt=prompt,
        created_at=datetime(2026, 11, 9, 8, 0, tzinfo=UTC),
        body="Yo soy cansado.",
        corrected="Estoy cansado.",
        errors=errors,
        segments=[Segment(SegmentKind.SAME, "Estoy cansado.")],
    )


def test_an_entry_view_counts_the_errors_and_labels_their_kinds() -> None:
    errors = [
        JournalError(ErrorKind.GRAMMAR, "ser_estar", "Yo soy", "Estoy", "Стан."),
        JournalError(ErrorKind.SPELLING, None, "hambe", "hambre", "Буква."),
    ]

    view = entry_view(_result("Записка сусідові", errors))

    assert (view.prompt, view.date, view.summary) == (
        "Записка сусідові",
        "09.11.2026",
        "Знайдено помилок: 2",
    )
    assert [error.kind for error in view.errors] == ["Граматика", "Правопис"]


def test_an_entry_without_a_prompt_or_errors_reads_as_a_clean_free_topic() -> None:
    view = entry_view(_result(None, []))

    assert (view.prompt, view.summary) == (FREE_TOPIC, "Помилок не знайдено")
