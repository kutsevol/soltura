import pytest

from soltura.learner.models import KnowledgeType
from soltura.practice.text import split_around
from soltura.warmup.service import WarmupItem, recall_before_recognize


def test_a_words_recall_card_comes_before_its_recognize_card() -> None:
    def item(card_id: int, lemma: str, knowledge_type: KnowledgeType) -> WarmupItem:
        return WarmupItem(
            card_id=card_id,
            knowledge_type=knowledge_type,
            lemma=lemma,
            sentence=f"Frase con {lemma}.",
            target_form=lemma,
        )

    queue = [
        item(1, "nieto", KnowledgeType.RECOGNIZE),
        item(2, "ir", KnowledgeType.RECALL),
        item(3, "nieto", KnowledgeType.RECALL),
        item(4, "ir", KnowledgeType.RECOGNIZE),
    ]

    assert [i.card_id for i in recall_before_recognize(queue)] == [3, 2, 1, 4]


@pytest.mark.parametrize(
    ("sentence", "form", "parts"),
    [
        ("Estoy seguro de que es verdad.", "es", ("Estoy seguro de que ", "es", " verdad.")),
        ("Vamos a ir a la playa.", "a", ("Vamos ", "a", " ir a la playa.")),
        ("Aunque llueve, salimos.", "aunque", ("", "Aunque", " llueve, salimos.")),
        ("Estoy en casa.", "es", None),
    ],
)
def test_the_target_form_is_found_only_as_a_whole_word(
    sentence: str, form: str, parts: tuple[str, str, str] | None
) -> None:
    assert split_around(sentence, form) == parts
