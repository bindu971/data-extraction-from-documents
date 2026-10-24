from pipeline.annotation_builder import locate_value


def test_exact_span():
    text = "The agreement starts on 12 March 2025."
    result = locate_value(text, "12 March 2025")
    assert result is not None
    assert text[result[0]:result[1]] == "12 March 2025"
