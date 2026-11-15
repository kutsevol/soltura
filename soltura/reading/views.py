import re
from collections.abc import Mapping
from dataclasses import dataclass

from soltura.reading.progress import ReadingProgress

GIST_LABEL = {
    "understood": "Ви зрозуміли текст",
    "partly": "Частково",
    "missed": "Схоже, текст не вдалося зрозуміти",
}


FACT_LABEL = {"correct": "Вірно", "partly": "Частково", "wrong": "Невірно"}


MAX_SHOWN_TRANSLATION = 16


def short_translation(translation: str) -> str:
    # The line above a word is a hint, not an entry: the first meaning, and no more than a
    # short word's width and a half, so a long gloss cannot push the words of its line apart.
    first = re.split(r"[,;(]", translation, maxsplit=1)[0].strip()
    if len(first) <= MAX_SHOWN_TRANSLATION:
        return first
    return f"{first[: MAX_SHOWN_TRANSLATION - 1].rstrip()}…"


@dataclass(frozen=True)
class Segment:
    text: str
    is_word: bool
    translation: str | None = None


_SENTENCE = re.compile(r"[^.!?…]+(?:[.!?…]+|$)\s*")
_WORD = re.compile(r"[^\W\d_]+|[\W\d_]+")


def split_for_reading(
    text: str, translations: Mapping[int, str] | None = None
) -> list[list[list[Segment]]]:
    # paragraphs -> sentences -> segments, so the page can send a tapped word
    # together with the sentence it appears in. `translations` is keyed by where a word
    # starts in `text`, the very string given here (not a trimmed or re-joined copy); a word
    # that starts there carries the short form of its translation.
    kept = translations or {}
    paragraphs: list[list[list[Segment]]] = []
    cursor = 0
    for paragraph in re.split(r"\n\s*\n", text):
        stripped = paragraph.strip()
        if not stripped:
            continue
        # Where this paragraph starts in the text, so each word has its position in it. The
        # paragraph is a slice of `text`, so it is always found; a miss would show a word
        # the wrong translation, so it fails loudly instead.
        base = text.index(stripped, cursor)
        cursor = base + len(stripped)
        sentences: list[list[Segment]] = []
        for match in _SENTENCE.finditer(stripped):
            sentence = match.group()
            if not sentence.strip():
                continue
            # The sentence pattern skips a stray full stop, so a sentence starts where its own
            # match does, not where the one before it ended.
            position = base + match.start()
            segments: list[Segment] = []
            for part in _WORD.findall(sentence):
                is_word = part[0].isalpha()
                translation = kept.get(position) if is_word else None
                segments.append(
                    Segment(
                        text=part,
                        is_word=is_word,
                        translation=short_translation(translation) if translation else None,
                    )
                )
                position += len(part)
            sentences.append(segments)
        paragraphs.append(sentences)
    return paragraphs


@dataclass(frozen=True)
class ProgressRow:
    title: str
    verdict: str
    taps_text: str
    too_hard: bool


@dataclass(frozen=True)
class ProgressView:
    score_text: str
    basis_text: str
    rows: list[ProgressRow]


def progress_view(progress: ReadingProgress) -> ProgressView:
    score = progress.score
    if score.percent is None:
        score_text = "Ще замало текстів для оцінки"
        basis_text = f"Відповідей на «Про що текст?»: {score.counted} із {score.needed} потрібних."
    else:
        score_text = f"Розуміння текстів: {score.percent}%"
        basis_text = f"За останніми текстами з відповіддю: {score.counted}."
    return ProgressView(
        score_text=score_text,
        basis_text=basis_text,
        rows=[
            ProgressRow(
                title=text.title,
                verdict=GIST_LABEL[text.gist] if text.gist else "",
                taps_text=f"Перевірено слів: {text.taps}",
                too_hard=text.below_target,
            )
            for text in progress.texts
        ],
    )
