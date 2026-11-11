import re
from dataclasses import dataclass

from soltura.reading.progress import ReadingProgress

GIST_LABEL = {
    "understood": "Ви зрозуміли текст",
    "partly": "Частково",
    "missed": "Схоже, текст не вдалося зрозуміти",
}


@dataclass(frozen=True)
class Segment:
    text: str
    is_word: bool


_SENTENCE = re.compile(r"[^.!?…]+(?:[.!?…]+|$)\s*")
_WORD = re.compile(r"[^\W\d_]+|[\W\d_]+")


def split_for_reading(text: str) -> list[list[list[Segment]]]:
    # paragraphs -> sentences -> segments, so the page can send a tapped word
    # together with the sentence it appears in.
    return [
        [
            [Segment(text=part, is_word=part[0].isalpha()) for part in _WORD.findall(sentence)]
            for sentence in _SENTENCE.findall(paragraph.strip())
            if sentence.strip()
        ]
        for paragraph in re.split(r"\n\s*\n", text)
        if paragraph.strip()
    ]


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
