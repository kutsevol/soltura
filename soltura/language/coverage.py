from collections import Counter
from collections.abc import Set
from dataclasses import dataclass

from soltura.language.nlp import Token


@dataclass(frozen=True)
class Coverage:
    ratio: float
    total_words: int
    unknown_lemmas: list[str]


def measure_coverage(tokens: list[Token], known_lemmas: Set[str]) -> Coverage:
    # Running words, not distinct ones: the 95-98% threshold (Hu & Nation 2000) is
    # defined over tokens, so an unknown word costs every time it appears.
    if not tokens:
        return Coverage(ratio=1.0, total_words=0, unknown_lemmas=[])

    unknown = Counter(token.lemma for token in tokens if token.lemma not in known_lemmas)
    known_count = len(tokens) - sum(unknown.values())
    return Coverage(
        ratio=known_count / len(tokens),
        total_words=len(tokens),
        unknown_lemmas=[lemma for lemma, _ in unknown.most_common()],
    )
