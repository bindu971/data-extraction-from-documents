from fastapi.testclient import TestClient

import service.api as api
from model.model_utils import load_field_config


DOCX = "assignment-1/data/test/156155545-Rental-Agreement-Kns-Home.pdf.docx"


class StubPredictor:
    """Replaces the Ollama call so the API can be tested offline."""

    def __init__(self):
        self.text = None

    def predict_text(self, text):
        self.text = text
        return {item["label"]: "x" for item in load_field_config()}


def make_client(monkeypatch):
    stub = StubPredictor()
    monkeypatch.setattr(api, "_predictor", stub)
    return TestClient(api.app), stub


def test_health_and_fields(monkeypatch):
    client, _ = make_client(monkeypatch)
    assert client.get("/health").json() == {"status": "ok"}
    assert len(client.get("/fields").json()["fields"]) == 6


def test_extract_docx_returns_six_fields(monkeypatch):
    client, stub = make_client(monkeypatch)
    with open(DOCX, "rb") as handle:
        response = client.post("/extract", files={"file": ("a.docx", handle)})

    assert response.status_code == 200
    assert len(response.json()["extracted_fields"]) == 6
    assert "RENTAL AGREEMENT" in stub.text


def test_extract_rejects_unsupported_type(monkeypatch):
    client, _ = make_client(monkeypatch)
    response = client.post("/extract", files={"file": ("a.pdf", b"data")})
    assert response.status_code == 400


class FailingPredictor:
    def predict_text(self, text):
        raise RuntimeError("Ollama is not running")


def test_extract_reports_model_failure(monkeypatch):
    monkeypatch.setattr(api, "_predictor", FailingPredictor())
    client = TestClient(api.app)
    with open(DOCX, "rb") as handle:
        response = client.post("/extract", files={"file": ("a.docx", handle)})

    assert response.status_code == 502
    assert "Ollama" in response.json()["detail"]
