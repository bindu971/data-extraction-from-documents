import json

import pytest

from model.model_utils import load_field_config
from model.ollama_extractor import OllamaExtractor, build_prompt, build_schema


FIELDS = load_field_config()
NAMES = [item["output_name"] for item in FIELDS]


def test_six_fields_configured():
    assert NAMES == [
        "Agreement Value",
        "Agreement Start Date",
        "Agreement End Date",
        "Renewal Notice (Days)",
        "Party One",
        "Party Two",
    ]


def test_schema_requires_exactly_the_six_fields():
    schema = build_schema(FIELDS)
    assert schema["required"] == NAMES
    assert set(schema["properties"]) == set(NAMES)


def test_prompt_contains_fields_and_document():
    prompt = build_prompt(FIELDS, "DOCUMENT TEXT")
    assert all(name in prompt for name in NAMES)
    assert prompt.endswith("DOCUMENT TEXT")


def test_extract_maps_output_names_to_labels(monkeypatch):
    extractor = OllamaExtractor()
    answer = {name: f"value {i}" for i, name in enumerate(NAMES)}
    monkeypatch.setattr(extractor, "_generate", lambda prompt: json.dumps(answer))

    result = extractor.extract("text")

    assert result["AGREEMENT_VALUE"] == "value 0"
    assert result["PARTY_TWO"] == "value 5"
    assert len(result) == 6


def test_extract_retries_invalid_json(monkeypatch):
    extractor = OllamaExtractor()
    replies = iter(["not json", json.dumps({"Party One": "A"})])
    monkeypatch.setattr(extractor, "_generate", lambda prompt: next(replies))

    result = extractor.extract("text")

    assert result["PARTY_ONE"] == "A"
    assert result["PARTY_TWO"] == ""


def test_extract_raises_after_repeated_failures(monkeypatch):
    extractor = OllamaExtractor()
    monkeypatch.setattr(extractor, "_generate", lambda prompt: "not json")

    with pytest.raises(RuntimeError):
        extractor.extract("text")
