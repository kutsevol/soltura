import re


def split_around(sentence: str, form: str) -> tuple[str, str, str] | None:
    # Whole words only: "es" must not match inside "Estoy", nor "a" inside "Vamos".
    match = re.search(rf"(?<!\w){re.escape(form)}(?!\w)", sentence, flags=re.IGNORECASE)
    if match is None:
        return None
    return sentence[: match.start()], match.group(0), sentence[match.end() :]
