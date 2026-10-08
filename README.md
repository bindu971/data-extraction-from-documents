# AI/ML Document Metadata Extraction

An AI/ML-based system that extracts the required metadata fields from rental agreement documents in `.docx` and image formats.

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

## Requirements

- Python 3.12
- Ollama
- Tesseract OCR for image input
- macOS/Linux/Windows environment capable of running the required Python packages

## Setup

Create and activate the Python virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Tesseract OCR

Tesseract is required when processing scanned image documents.

On macOS:

```bash
brew install tesseract
```

Verify the installation:

```bash
tesseract --version
```

## Ollama Setup

The prediction and API stages use a locally hosted Ollama language model.

Install Ollama and make sure the Ollama service is running.

Verify the installation:

```bash
ollama --version
```

Check the locally available models:

```bash
ollama list
```

The model configuration used by the project is defined in:

```text
model/ollama_extractor.py
```

The Ollama model must be available before running prediction or the API.

## Dataset

Training documents are stored in:

```text
assignment-1/data/train/
```

Test documents are stored in:

```text
assignment-1/data/test/
```

The corresponding metadata files are:

```text
assignment-1/data/train.csv
assignment-1/data/test.csv
```

The dataset contains the six target fields required by the assignment.

## Training

Run the training pipeline with:

```bash
python train_pipeline.py
```

The pipeline prepares the training examples and generates artifacts under:

```text
artifacts/
```

Generated artifacts can include:

```text
artifacts/train_examples.json
artifacts/test_examples.json
artifacts/train.spacy
artifacts/test.spacy
artifacts/ner_model/
```

## Prediction

Make sure Ollama is running before starting prediction.

Run:

```bash
python predict_documents.py
```

The predictions are saved to:

```text
outputs/predictions.csv
```

The prediction file contains the expected and predicted values for the six required fields.

## Evaluation

Run:

```bash
python -m evaluation.evaluate_predictions
```

The evaluation calculates per-field:

- Precision
- Recall
- F1 score

The main metric specified by the assignment is **per-field exact-match recall**.

Exact-match recall is calculated using the number of correct predictions compared with the number of non-empty ground-truth values.

The evaluation report is saved to:

```text
outputs/evaluation_report.json
```

## API

The project also provides a FastAPI service for document extraction.

Start the API with:

```bash
uvicorn service.api:app --reload
```

Open the Swagger UI:

```text
http://127.0.0.1:8000/docs
```

The API provides:

```text
GET  /health
GET  /fields
POST /extract
```

The `/extract` endpoint accepts:

- `.docx`
- `.png`
- `.jpg`
- `.jpeg`

The response contains the six extracted metadata fields as structured JSON.

Example response:

```json
{
  "filename": "sample-agreement.docx",
  "extracted_fields": {
    "Agreement Value": "12000",
    "Agreement Start Date": "01.04.2008",
    "Agreement End Date": "31.03.2009",
    "Renewal Notice (Days)": "60",
    "Party One": "Hanumaiah",
    "Party Two": "Vishal Bhardwaj"
  }
}
```

## Technologies Used

- Python
- Ollama
- spaCy
- PyTorch
- Pandas
- FastAPI
- Tesseract OCR
- scikit-learn

## Assignment

This project was developed as a solution for the **Meta Data Extraction from Documents** AI/ML assignment.

The assignment requires extracting:

- Agreement Value
- Agreement Start Date
- Agreement End Date
- Renewal Notice (Days)
- Party One
- Party Two

from documents with different layouts.

The system is designed to extract these fields based on the document content rather than depending on one fixed document template or regular-expression-based extraction.

## Project Outputs

After running the pipeline, the main outputs are:

```text
outputs/
├── predictions.csv
└── evaluation_report.json
```

These files contain the model predictions and evaluation results for the test documents.

## Notes

- OCR is used for scanned image documents.
- DOCX documents are processed directly for text extraction.
- Ollama is used for the current prediction stage.
- The extraction stage does not use regular expressions to determine field values.
- The project separates document loading, preprocessing, model prediction, evaluation, and API functionality into different modules.
