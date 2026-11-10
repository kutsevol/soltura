import re
from dataclasses import dataclass

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
