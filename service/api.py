from pathlib import Path
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException

from pipeline.document_loader import load_document
from pipeline.text_cleaner import clean_text
from model.predictor import MetadataPredictor
from model.model_utils import load_field_config


app = FastAPI(
    title="Contract Field Extraction API",
    version="1.0.0",
    description="AI/ML-based extraction of contract metadata fields."
)

_predictor = None


def predictor():
    global _predictor
    if _predictor is None:
        _predictor = MetadataPredictor()
    return _predictor


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/fields")
def fields():
    return {
        "fields": [item["output_name"] for item in load_field_config()]
    }


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()

    if suffix not in {".docx", ".png", ".jpg", ".jpeg"}:
        raise HTTPException(
            status_code=400,
            detail="Supported files: .docx, .png, .jpg, .jpeg",
        )

    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        handle.write(contents)
        temp_path = Path(handle.name)

    try:
        text = clean_text(load_document(temp_path))
        labels = predictor().predict_text(text)

        field_map = load_field_config()
        result = {
            item["output_name"]: labels.get(item["label"])
            for item in field_map
        }

        return {
            "filename": file.filename,
            "extracted_fields": result,
        }
    finally:
        temp_path.unlink(missing_ok=True)
