from dataclasses import dataclass

from soltura.words.vocabulary import OPEN_END, BandProgress, VocabularyMap

# One word in a band of hundreds is under a percent: it still gets a sliver the eye can
# see and a label that says "some", not "none".
MIN_VISIBLE_WIDTH = 1.0


@dataclass(frozen=True)
class BandView:
    label: str
    known_width: float
    learning_width: float
    share_label: str
    description: str


@dataclass(frozen=True)
class VocabularyView:
    headline: str
    bands: list[BandView]


def _number(value: int) -> str:
    return f"{value:,}".replace(",", " ")


def _percent(part: int, whole: int) -> float:
    return 100 * part / whole if whole else 0.0


def _width(percent: float) -> float:
    return round(max(percent, MIN_VISIBLE_WIDTH), 1) if percent > 0 else 0.0


def _share_label(percent: float) -> str:
    rounded = round(percent)
    return "<1%" if percent > 0 and rounded == 0 else f"{rounded}%"


def _band_view(band: BandProgress) -> BandView:
    label = f"{band.min_rank}+" if band.max_rank == OPEN_END else f"{band.min_rank}–{band.max_rank}"
    known = _percent(band.known, band.total)
    learning = _percent(band.learning, band.total)
    return BandView(
        label=label,
        known_width=_width(known),
        learning_width=_width(learning),
        share_label=_share_label(known + learning),
        description=(f"Слова {label}: знаю {_share_label(known)}, вивчаю {_share_label(learning)}"),
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
