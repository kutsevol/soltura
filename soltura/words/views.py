from dataclasses import dataclass

from soltura.words.vocabulary import OPEN_END, BandProgress, VocabularyMap


@dataclass(frozen=True)
class BandView:
    label: str
    known_width: float
    learning_width: float
    share: int
    description: str


@dataclass(frozen=True)
class VocabularyView:
    headline: str
    bands: list[BandView]


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _percent(part: int, whole: int) -> float:
    return round(100 * part / whole, 1) if whole else 0.0


def _band_view(band: BandProgress) -> BandView:
    label = f"{band.min_rank}+" if band.max_rank == OPEN_END else f"{band.min_rank}–{band.max_rank}"
    known = _percent(band.known, band.total)
    learning = _percent(band.learning, band.total)
    return BandView(
        label=label,
        known_width=known,
        learning_width=learning,
        share=round(known + learning),
        description=f"Слова {label}: знаю {round(known)}%, вивчаю {round(learning)}%",
    )


def known_summary(vocabulary: VocabularyMap) -> str:
    return f"Знаю слів: {_number(vocabulary.known)} з {_number(vocabulary.total)}"


def vocabulary_view(vocabulary: VocabularyMap) -> VocabularyView:
    return VocabularyView(
        headline=(
            f"Карта словника · знаю {_number(vocabulary.known)} з {_number(vocabulary.total)}"
        ),
        bands=[_band_view(band) for band in vocabulary.bands],
    )
