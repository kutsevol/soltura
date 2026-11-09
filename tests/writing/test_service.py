from soltura.learner.models import ErrorKind
from soltura.learner.repository import JournalError
from soltura.writing.service import (
    Correction,
    FoundError,
    Segment,
    SegmentKind,
    correct_text,
    diff_segments,
)
from tests.fakes import FakeLLM

UNITS = {"ser_estar": "Ser і estar"}
TEXT = "Yo soy cansado porque trabajo mucho."
FIXED = "Estoy cansado porque trabajo mucho."


def found(original: str, corrected: str, category: str = "ser_estar") -> FoundError:
    return FoundError(original=original, corrected=corrected, category=category, note="пояснення")


async def test_an_error_whose_fragment_is_not_in_the_text_is_dropped(llm: FakeLLM) -> None:
    llm.answer(
        Correction(
            corrected_text=FIXED,
            errors=[found("Yo soy", "Estoy"), found("tengo hambre", "tenía hambre")],
        )
    )

    result = await correct_text(llm, TEXT, UNITS)

    assert result.errors == [
        JournalError(ErrorKind.GRAMMAR, "ser_estar", "Yo soy", "Estoy", "пояснення")
    ]


async def test_an_unknown_grammar_unit_id_is_filed_as_other(llm: FakeLLM) -> None:
    llm.answer(
        Correction(
            corrected_text=FIXED,
            errors=[
                found("Yo soy", "Estoy", "made_up_unit"),
                found("mucho", "muchísimo", "spelling"),
            ],
        )
    )

    result = await correct_text(llm, TEXT, UNITS)

    assert [(error.kind, error.unit_id) for error in result.errors] == [
        (ErrorKind.OTHER, None),
        (ErrorKind.SPELLING, None),
    ]


async def test_a_fix_that_changes_nothing_is_dropped(llm: FakeLLM) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[found("mucho", "mucho")]))

    result = await correct_text(llm, TEXT, UNITS)

    assert result.errors == []


async def test_a_text_without_errors_comes_back_unchanged(llm: FakeLLM) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    result = await correct_text(llm, TEXT, UNITS)

    assert result.corrected == TEXT
    assert result.segments == [Segment(SegmentKind.SAME, TEXT)]


async def test_the_prompt_lists_the_grammar_units_and_the_text(llm: FakeLLM) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    await correct_text(llm, TEXT, UNITS)

    assert "- ser_estar: Ser і estar" in llm.prompts[0]
    assert TEXT in llm.prompts[0]


def test_the_diff_marks_removed_and_added_words() -> None:
    segments = diff_segments(TEXT, FIXED)

    assert segments == [
        Segment(SegmentKind.REMOVED, "Yo soy"),
        Segment(SegmentKind.ADDED, "Estoy"),
        Segment(SegmentKind.SAME, " cansado porque trabajo mucho."),
    ]


def test_the_diff_marks_a_removed_word_without_an_added_one() -> None:
    segments = diff_segments("Voy a a casa.", "Voy a casa.")

    assert (
        Segment(SegmentKind.REMOVED, "a ") in segments
        or Segment(SegmentKind.REMOVED, " a") in segments
    )
    assert "".join(s.text for s in segments if s.kind != SegmentKind.ADDED) == "Voy a a casa."
    assert "".join(s.text for s in segments if s.kind != SegmentKind.REMOVED) == "Voy a casa."
