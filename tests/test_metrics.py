from evaluation.metrics import exact_match, field_metrics


def test_exact_match_ignores_only_whitespace():
    assert exact_match(" Hanumaiah ", "Hanumaiah")
    assert not exact_match("KAPIL MEHROTRA", "Kapil Mehrotra")
    assert not exact_match("60", "60.0")


def test_missing_prediction_counts_as_false():
    rows = [
        {"Field_expected": "60", "Field_predicted": "60"},
        {"Field_expected": "30", "Field_predicted": ""},
    ]
    report = field_metrics(rows, ["Field"])
    assert report["Field"]["recall"] == 0.5
