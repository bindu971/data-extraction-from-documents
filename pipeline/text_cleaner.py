import unicodedata


def clean_text(value: str) -> str:
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Preserve meaningful punctuation but remove invisible/control characters.
    text = "".join(
        char for char in text
        if char == "\n" or not unicodedata.category(char).startswith("C")
    )

    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(line for line in lines if line)


def clean_value(value) -> str:
    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    return " ".join(text.split()).strip()
