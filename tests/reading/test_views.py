from soltura.reading.views import split_for_reading


def test_split_for_reading_keeps_each_word_with_its_sentence() -> None:
    paragraphs = split_for_reading("Ayer fue al médico. ¿Qué te dijo?\n\nNada, todo bien.")

    sentences = [["".join(s.text for s in sentence).strip() for sentence in p] for p in paragraphs]
    assert sentences == [["Ayer fue al médico.", "¿Qué te dijo?"], ["Nada, todo bien."]]
    words = [s.text for s in paragraphs[0][1] if s.is_word]
    assert words == ["Qué", "te", "dijo"]
