import pytest

from soltura.reading.service import text_length


@pytest.mark.parametrize(
    ("vocabulary", "length"),
    [(250, "About 50 words"), (500, "About 120 to 180 words"), (3000, "About 120 to 180 words")],
)
def test_only_the_first_band_gets_the_short_text(vocabulary: int, length: str) -> None:
    assert text_length(vocabulary) == length
