import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import StrEnum

from pydantic import BaseModel, Field

from soltura.learner.models import ErrorKind
from soltura.learner.repository import JournalError
from soltura.llm.client import LLMClient

MIN_LENGTH = 20
MAX_LENGTH = 1_000
# Errors in one grammar unit after which the unit is offered; fewer may be chance.
SUGGEST_AFTER = 3

# Error kinds the model may name besides a grammar unit id.
OTHER_KINDS = {kind.value: kind for kind in ErrorKind if kind != ErrorKind.GRAMMAR}

TOKEN = re.compile(r"\w+|\s+|[^\w\s]")

CORRECTION_SYSTEM = (
    "You correct a short Spanish text written by a Ukrainian-speaking learner at level A2 to B1 "
    "who lives in Spain. Fix only what is wrong and keep the learner's meaning, words and style "
    "wherever they are acceptable Spanish. Return the whole corrected text and the list of errors "
    "you fixed. For each error, 'original' is the smallest fragment copied exactly, character for "
    "character, from the learner's text; 'corrected' is that fragment after the fix, empty when "
    "the fragment should be removed; 'category' is one of the ids you are given; 'note' is one "
    "short sentence in Ukrainian saying why the original is wrong. Choose a grammar unit id only "
    "when that unit's rule explains the error. If the text has no errors, return it unchanged "
    "with an empty list."
)


class TextProblem(StrEnum):
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"


class InvalidText(Exception):
    def __init__(self, problem: TextProblem) -> None:
        super().__init__(problem.value)
        self.problem = problem


class SegmentKind(StrEnum):
    SAME = "same"
    REMOVED = "removed"
    ADDED = "added"


@dataclass(frozen=True)
class Segment:
    kind: SegmentKind
    text: str


@dataclass(frozen=True)
class CorrectedText:
    corrected: str
    errors: list[JournalError]
    segments: list[Segment]


class FoundError(BaseModel):
    original: str = Field(description="The smallest fragment of the learner's text that is wrong")
    corrected: str = Field(description="The fragment after the fix; empty to remove it")
    category: str = Field(description="Id of the grammar unit, or vocabulary, spelling or other")
    note: str = Field(description="One sentence in Ukrainian saying why the original is wrong")


class Correction(BaseModel):
    corrected_text: str = Field(description="The whole text after the corrections")
    errors: list[FoundError] = Field(description="The errors fixed, in the order of the text")


def check_length(text: str) -> None:
    if len(text) < MIN_LENGTH:
        raise InvalidText(TextProblem.TOO_SHORT)
    if len(text) > MAX_LENGTH:
        raise InvalidText(TextProblem.TOO_LONG)


def correction_prompt(text: str, units: Mapping[str, str]) -> str:
    categories = [f"- {unit_id}: {title}" for unit_id, title in units.items()]
    categories += [
        "- vocabulary: a wrong or missing word",
        "- spelling: accents and letters",
        "- other: anything else",
    ]
    return "Categories:\n" + "\n".join(categories) + f"\n\nThe learner's text:\n{text}"


def _category(category: str, units: Mapping[str, str]) -> tuple[ErrorKind, str | None]:
    if category in units:
        return ErrorKind.GRAMMAR, category
    return OTHER_KINDS.get(category, ErrorKind.OTHER), None


def verified_errors(
    text: str, correction: Correction, units: Mapping[str, str]
) -> list[JournalError]:
    errors: list[JournalError] = []
    for found in correction.errors:
        original = found.original.strip()
        fixed = found.corrected.strip()
        # An error is kept only when code can find it in the text and the fix changes it.
        if not original or original == fixed or original not in text:
            continue
        kind, unit_id = _category(found.category.strip(), units)
        errors.append(JournalError(kind, unit_id, original, fixed, found.note.strip()))
    return errors


def diff_segments(before: str, after: str) -> list[Segment]:
    old = TOKEN.findall(before)
    new = TOKEN.findall(after)
    segments: list[Segment] = []

    def add(kind: SegmentKind, text: str) -> None:
        if not text:
            return
        if segments and segments[-1].kind == kind:
            segments[-1] = Segment(kind, segments[-1].text + text)
        else:
            segments.append(Segment(kind, text))

    for tag, old_start, old_end, new_start, new_end in SequenceMatcher(
        None, old, new, autojunk=False
    ).get_opcodes():
        if tag == "equal":
            add(SegmentKind.SAME, "".join(old[old_start:old_end]))
        else:
            add(SegmentKind.REMOVED, "".join(old[old_start:old_end]))
            add(SegmentKind.ADDED, "".join(new[new_start:new_end]))
    return segments


async def correct_text(llm: LLMClient, text: str, units: Mapping[str, str]) -> CorrectedText:
    correction = await llm(
        Correction,
        system=CORRECTION_SYSTEM,
        prompt=correction_prompt(text, units),
        effort="medium",
        max_tokens=8_000,
    )
    corrected = correction.corrected_text.strip() or text
    return CorrectedText(
        corrected=corrected,
        errors=verified_errors(text, correction, units),
        segments=diff_segments(text, corrected),
    )


@dataclass(frozen=True)
class ErrorCategory:
    kind: ErrorKind
    unit_id: str | None
    title: str | None
    count: int
    last: JournalError
    suggested: bool


def build_error_summary(
    errors: Sequence[JournalError], unit_titles: Mapping[str, str]
) -> list[ErrorCategory]:
    # unit_titles must be in teaching order: the order of its keys breaks ties between counts.
    teaching_order = {unit_id: index for index, unit_id in enumerate(unit_titles)}
    kind_order = {kind: len(teaching_order) + index for index, kind in enumerate(ErrorKind)}
    grouped: dict[tuple[ErrorKind, str | None], list[JournalError]] = {}
    for error in errors:
        known = error.kind == ErrorKind.GRAMMAR and error.unit_id in unit_titles
        unit_id = error.unit_id if known else None
        grouped.setdefault((error.kind, unit_id), []).append(error)
    categories = [
        ErrorCategory(
            kind=kind,
            unit_id=unit_id,
            title=unit_titles[unit_id] if unit_id else None,
            count=len(group),
            last=group[-1],
            suggested=unit_id is not None and len(group) >= SUGGEST_AFTER,
        )
        for (kind, unit_id), group in grouped.items()
    ]
    return sorted(
        categories,
        key=lambda category: (
            -category.count,
            teaching_order[category.unit_id] if category.unit_id else kind_order[category.kind],
        ),
    )
