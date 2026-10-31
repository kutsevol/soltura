import pytest

from soltura.config import settings
from soltura.llm.client import get_llm
from soltura.reading.service import GLOSS_SYSTEM, Gloss

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(settings.llm.api_key is None, reason="needs ANTHROPIC_API_KEY"),
]


@pytest.mark.parametrize(
    ("word", "sentence", "lemma"),
    [
        ("fue", "Ayer fue al médico.", "ir"),
        ("fue", "La película fue buena.", "ser"),
        ("Como", "Como pan todos los días.", "comer"),
        ("vengas", "Quiero que vengas.", "venir"),
    ],
)
async def test_the_gloss_lemmatizes_a_tapped_word_by_its_context(
    word: str, sentence: str, lemma: str
) -> None:
    gloss = await get_llm()(
        Gloss,
        system=GLOSS_SYSTEM,
        prompt=f"Word: {word}\nSentence: {sentence}",
        effort="low",
        max_tokens=4_000,
    )

    assert gloss.lemma.strip().lower() == lemma
    assert gloss.translation.strip()
