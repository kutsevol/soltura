from dataclasses import dataclass
from functools import cache

import spacy
from spacy.language import Language
from spacy.tokens import Token as SpacyToken

MODEL = "es_core_news_md"

# Tags that never count as vocabulary: a name or a number in a text is not a word
# the learner has to know.
SKIPPED_POS = frozenset({"PUNCT", "SYM", "NUM", "PROPN", "SPACE", "X"})


@dataclass(frozen=True)
class Token:
    text: str
    lemma: str
    pos: str


@cache
def load_pipeline() -> Language:
    return spacy.load(MODEL, exclude=["ner", "parser"])


def _counts_as_word(token: SpacyToken, skipped_pos: frozenset[str]) -> bool:
    return token.pos_ not in skipped_pos and token.is_alpha


def _to_token(token: SpacyToken) -> Token:
    return Token(text=token.text, lemma=token.lemma_.lower(), pos=token.pos_)


def analyze(text: str) -> list[Token]:
    return [
        _to_token(token) for token in load_pipeline()(text) if _counts_as_word(token, SKIPPED_POS)
    ]


def analyze_words(words: list[str], batch_size: int = 1000) -> list[list[Token]]:
    # A word on its own has no context, and the tagger often calls a common lowercase
    # noun such as "casa" a proper noun, so isolated words keep their PROPN tokens.
    skipped_pos = SKIPPED_POS - {"PROPN"}
    return [
        [_to_token(token) for token in doc if _counts_as_word(token, skipped_pos)]
        for doc in load_pipeline().pipe(words, batch_size=batch_size)
    ]
