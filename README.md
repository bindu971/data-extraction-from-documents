# Contract Field Extractor

An independent AI/ML document metadata extraction pipeline for `.docx`, `.png`,
and `.jpg` documents.

## Target fields

- Agreement Value
- Agreement Start Date
- Agreement End Date
- Renewal Notice (Days)
- Party One
- Party Two

## Design

The pipeline is deliberately modular:

1. Read documents and ground-truth CSV files.
2. Extract text from DOCX or OCR-supported images.
3. Prepare training examples from labeled metadata.
4. Align labeled values to text using fuzzy character-span matching.
5. Use an AI/ML extraction model to predict fields from unseen documents.
6. Validate and evaluate the extracted fields.
7. Evaluate exact-match recall and additional precision/F1 statistics.
8. Expose extraction through FastAPI.

The extraction model does not use regular expressions or document-specific
templates to decide the answer. The current prediction stage uses a local
Ollama-hosted language model and structured JSON output.

## Project layout

```text
contract_field_extractor/
├── dataset/
│   ├── training_docs/
│   ├── evaluation_docs/
│   ├── train.csv
│   └── test.csv
├── artifacts/
├── configs/
│   └── extraction_fields.json
├── pipeline/
│   ├── document_loader.py
│   ├── image_reader.py
│   ├── text_cleaner.py
│   ├── annotation_builder.py
│   └── dataset_writer.py
├── model/
│   ├── ner_trainer.py
│   ├── predictor.py
│   └── model_utils.py
├── evaluation/
│   ├── metrics.py
│   └── evaluate_predictions.py
├── service/
│   └── api.py
├── tests/
├── outputs/
├── train_pipeline.py
├── predict_documents.py
├── requirements.txt
└── .env.example
```

## Setup

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Tesseract is required only for image input.

macOS:

```bash
brew install tesseract
```

## Dataset placement

Put training documents in:

```text
assignment-1/data/train/
```

Put test documents in:

```text
assignment-1/data/test/
```

Place the corresponding metadata files at:

```text
assignment-1/data/train.csv
assignment-1/data/test.csv
```

The loader accepts common filename columns such as `filename`, `file_name`,
`document`, `document_name`, or `id`, and recognizes the six target fields
including the common `Aggrement Value` typo.

## Train

```bash
python train_pipeline.py
```

This creates:

```text
artifacts/train_examples.json
artifacts/test_examples.json
artifacts/train.spacy
artifacts/test.spacy
artifacts/ner_model/
```

## Predict

```bash
python predict_documents.py
```

Results are written to:

```text
outputs/predictions.csv
```

## Evaluate

```bash
python -m evaluation.evaluate_predictions
```

The main assignment metric is per-field exact-match recall:

`correct exact matches / number of non-empty ground-truth values`

## API

```bash
uvicorn service.api:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

POST a document to `/extract`.

## Notes

This project is intentionally different from a simple copied notebook:
configuration, document loading, annotation alignment, model training,
prediction and evaluation are separate modules.
