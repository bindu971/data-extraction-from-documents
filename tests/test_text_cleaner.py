from pipeline.text_cleaner import clean_text, clean_value


def test_clean_value():
    assert clean_value("  Alpha   Beta ") == "Alpha Beta"


def test_clean_text():
    value = "Hello\r\nWorld\n\nSecond line"
    assert clean_text(value) == "Hello\nWorld\nSecond line"
