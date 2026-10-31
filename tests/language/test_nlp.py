from soltura.language.nlp import analyze, analyze_words


def test_analyze_skips_punctuation_numbers_and_names() -> None:
    tokens = analyze("Ayer fue al médico con Juan, a las 3.")

    assert [token.text for token in tokens] == ["Ayer", "fue", "al", "médico", "con", "a", "las"]


def test_analyze_returns_lowercase_lemmas() -> None:
    tokens = analyze("Compré pan.")

    assert [token.lemma for token in tokens] == ["comprar", "pan"]


def test_analyze_words_keeps_nouns_the_tagger_calls_names_out_of_context() -> None:
    [casa] = analyze_words(["casa"])

    assert [token.lemma for token in casa] == ["casa"]
