from soltura.learner.models import ErrorKind
from soltura.learner.repository import JournalError
from soltura.writing.service import (
    Correction,
    FoundError,
    Segment,
    SegmentKind,
    build_error_summary,
    correct_text,
    diff_segments,
    words_written_correctly,
)
from tests.fakes import FakeLLM

UNITS = {"ser_estar": "Ser і estar"}
TEXT = "Yo soy cansado porque trabajo mucho."
FIXED = "Estoy cansado porque trabajo mucho."
VOCABULARY = 3000


def found(original: str, corrected: str, category: str = "ser_estar") -> FoundError:
    return FoundError(original=original, corrected=corrected, category=category, note="пояснення")


async def test_an_error_whose_fragment_is_not_in_the_text_is_dropped(llm: FakeLLM) -> None:
    llm.answer(
        Correction(
            corrected_text=FIXED,
            errors=[found("Yo soy", "Estoy"), found("tengo hambre", "tenía hambre")],
        )
    )

    result = await correct_text(llm, TEXT, UNITS, VOCABULARY)

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

    result = await correct_text(llm, TEXT, UNITS, VOCABULARY)

    assert [(error.kind, error.unit_id) for error in result.errors] == [
        (ErrorKind.OTHER, None),
        (ErrorKind.SPELLING, None),
    ]


async def test_a_fix_that_changes_nothing_is_dropped(llm: FakeLLM) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[found("mucho", "mucho")]))

    result = await correct_text(llm, TEXT, UNITS, VOCABULARY)

    assert result.errors == []


async def test_a_text_without_errors_comes_back_unchanged(llm: FakeLLM) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    result = await correct_text(llm, TEXT, UNITS, VOCABULARY)

    assert result.corrected == TEXT
    assert result.segments == [Segment(SegmentKind.SAME, TEXT)]


async def test_the_prompt_lists_the_grammar_units_and_the_text(llm: FakeLLM) -> None:
    llm.answer(Correction(corrected_text=TEXT, errors=[]))

    await correct_text(llm, TEXT, UNITS, VOCABULARY)

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


UNIT_TITLES = {"ser_estar": "Ser і estar", "por_para": "Por і para"}


def _grammar(unit_id: str | None, original: str = "x", corrected: str = "y") -> JournalError:
    return JournalError(ErrorKind.GRAMMAR, unit_id, original, corrected, "")


def test_the_summary_counts_errors_per_unit_and_keeps_the_last_example() -> None:
    errors = [_grammar("por_para", "a", "b"), _grammar("ser_estar", "c", "d")]
    errors += [_grammar("ser_estar", "e", "f"), _grammar("ser_estar", "g", "h")]

    summary = build_error_summary(errors, UNIT_TITLES)

    assert [(c.unit_id, c.title, c.count, c.last.original) for c in summary] == [
        ("ser_estar", "Ser і estar", 3, "g"),
        ("por_para", "Por і para", 1, "a"),
    ]


def test_a_unit_is_suggested_only_from_three_errors() -> None:
    errors = [_grammar("ser_estar")] * 3 + [_grammar("por_para")] * 2

    summary = build_error_summary(errors, UNIT_TITLES)

    assert {c.unit_id: c.suggested for c in summary} == {"ser_estar": True, "por_para": False}


def test_equal_counts_follow_the_teaching_order_and_other_kinds_come_last() -> None:
    errors = [
        JournalError(ErrorKind.SPELLING, None, "a", "b", ""),
        _grammar("por_para"),
        _grammar("ser_estar"),
    ]

    summary = build_error_summary(errors, UNIT_TITLES)

    assert [(c.unit_id, c.kind) for c in summary] == [
        ("ser_estar", ErrorKind.GRAMMAR),
        ("por_para", ErrorKind.GRAMMAR),
        (None, ErrorKind.SPELLING),
    ]


def test_a_grammar_error_of_a_removed_unit_stays_without_a_lesson_or_a_suggestion() -> None:
    summary = build_error_summary([_grammar("gone")] * 4, UNIT_TITLES)

    assert [(c.unit_id, c.title, c.count, c.suggested) for c in summary] == [(None, None, 4, False)]


def test_a_frequent_spelling_error_ranks_above_a_rarer_unit() -> None:
    errors = [JournalError(ErrorKind.SPELLING, None, "a", "b", "")] * 3 + [_grammar("ser_estar")]

    summary = build_error_summary(errors, UNIT_TITLES)

    assert [(c.kind, c.count) for c in summary] == [(ErrorKind.SPELLING, 3), (ErrorKind.GRAMMAR, 1)]


def test_words_inside_an_error_fragment_are_not_counted_as_written_right() -> None:
    errors = [JournalError(ErrorKind.GRAMMAR, "ser_estar", "Yo soy", "Estoy", "")]

    lemmas = words_written_correctly("Yo soy cansado porque trabajo mucho.", errors)

    assert {"cansar", "trabajar", "mucho"} <= lemmas
    assert not {"ser", "yo"} & lemmas


def test_a_word_is_matched_by_its_form_when_the_fragment_gives_it_another_lemma() -> None:
    errors = [JournalError(ErrorKind.VOCABULARY, None, "vino", "vinho", "")]

    lemmas = words_written_correctly("Quiero vino", errors)

    assert lemmas == {"querer"}
