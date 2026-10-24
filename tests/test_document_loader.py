from pathlib import Path

import pytest

from pipeline.document_loader import load_document
from predict_documents import resolve_document


TEST_DIR = Path("assignment-1/data/test")


def test_resolve_document_finds_docx_and_png():
    docx = resolve_document(TEST_DIR, "156155545-Rental-Agreement-Kns-Home")
    png = resolve_document(TEST_DIR, "24158401-Rental-Agreement")
    assert docx.name.endswith(".pdf.docx")
    assert png.suffix == ".png"
    assert resolve_document(TEST_DIR, "does-not-exist") is None


def test_load_docx_text():
    text = load_document(TEST_DIR / "156155545-Rental-Agreement-Kns-Home.pdf.docx")
    assert "RENTAL AGREEMENT" in text


def test_unsupported_extension():
    with pytest.raises(ValueError):
        load_document("file.pdf")
