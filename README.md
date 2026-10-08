# AI/ML Document Metadata Extraction

An AI/ML-based system that extracts important metadata from rental agreement documents in `.docx` and image formats.

## Fields Extracted

- Agreement Value
- Agreement Start Date
- Agreement End Date
- Renewal Notice (Days)
- Party One
- Party Two

## How It Works

The project processes a document through the following steps:

1. Read the input DOCX or image.
2. Extract text from DOCX files or use OCR for images.
3. Prepare labeled training data from the provided metadata.
4. Create training examples by matching metadata values with document text.
5. Use an AI/ML model to extract the required fields.
6. Validate the extracted values.
7. Compare predictions with the test dataset using exact-match evaluation.
8. Provide the extraction functionality through a FastAPI endpoint.

The prediction stage uses a locally hosted Ollama language model and returns the extracted fields as structured JSON.

No regular expressions or document-specific templates are used to determine the extracted values.

## Project Structure

```text
data-extraction-from-documents/
├── assignment-1/
│   ├── data/
│   │   ├── train/
│   │   ├── test/
│   │   ├── train.csv
│   │   └── test.csv
│   └── assignment-details.pdf
├── artifacts/
├── configs/
├── evaluation/
├── model/
├── outputs/
├── pipeline/
├── service/
├── tests/
├── predict_documents.py
├── train_pipeline.py
├── requirements.txt
└── README.md
```

## Setup

Create and activate the Python environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

For image input, install Tesseract OCR on macOS:

```bash
brew install tesseract
```

## Dataset

Training documents:

```text
assignment-1/data/train/
```

Test documents:

```text
assignment-1/data/test/
```

Metadata files:

```text
assignment-1/data/train.csv
assignment-1/data/test.csv
```

## Training

Run:

```bash
python train_pipeline.py
```

Training artifacts are generated under:

```text
artifacts/
```

## Prediction

Run:

```bash
python predict_documents.py
```

Predictions are saved to:

```text
outputs/predictions.csv
```

## Evaluation

Run:

```bash
python -m evaluation.evaluate_predictions
```

The main evaluation metric for the assignment is **per-field exact-match recall**.

Additional precision and F1 scores are also reported.

## API

Start the FastAPI application:

```bash
uvicorn service.api:app --reload
```

Open the Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Upload a `.docx`, `.png`, `.jpg`, or `.jpeg` document to the `/extract` endpoint.

The API returns the six extracted metadata fields as JSON.

## Technologies Used

- Python
- spaCy
- Ollama
- OCR / Tesseract
- FastAPI
- Pandas
- PyTorch
- scikit-learn

## Assignment

This project was developed as a solution for the **Meta Data Extraction from Documents** AI/ML assignment.

The system is designed to handle documents with different layouts rather than depending on one fixed document template.
