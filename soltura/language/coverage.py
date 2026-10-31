import math
from collections import Counter
from collections.abc import Mapping, Set
from dataclasses import dataclass, field

from soltura.language.nlp import Token


@dataclass(frozen=True)
class Coverage:
    ratio: float
    total_words: int
    unknown_lemmas: list[str]
    unknown_counts: dict[str, int] = field(default_factory=dict)


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
        unknown_counts=dict(unknown.most_common()),
    )


def words_to_replace(coverage: Coverage, ranks: Mapping[str, int], target: float) -> list[str]:
    # A text at the target still holds a few unknown words, and those are what the
    # learner meets for the first time. Only the excess goes, rarest first; a lemma
    # with no frequency rank counts as the rarest.
    allowed = math.floor(coverage.total_words * (1 - target))
    excess = sum(coverage.unknown_counts.values()) - allowed
    if excess <= 0:
        return []
    rarest_first = sorted(
        coverage.unknown_counts, key=lambda lemma: ranks.get(lemma, math.inf), reverse=True
    )
    chosen: list[str] = []
    for lemma in rarest_first:
        if excess <= 0:
            break
        chosen.append(lemma)
        excess -= coverage.unknown_counts[lemma]
    return chosen
