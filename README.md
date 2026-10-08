# AI/ML Document Metadata Extraction

Extracts six metadata fields from rental agreements in `.docx` or scanned image (`.png`, `.jpg`, `.jpeg`) format, regardless of the document's template or layout.

## Fields Extracted

1. Agreement Value
2. Agreement Start Date
3. Agreement End Date
4. Renewal Notice (Days)
5. Party One
6. Party Two

## Solution Approach

```text
DOCX     → document loader (python-docx) → text cleaning → Ollama extraction → six fields (JSON)
PNG/JPG  → Tesseract OCR                 → text cleaning → Ollama extraction → six fields (JSON)
```

1. **Document loading** – `.docx` files are read with python-docx (paragraphs and table rows). Scanned images are converted to text with Tesseract OCR.
2. **Text cleaning** – Unicode normalisation (NFKC), removal of control characters and collapsing of whitespace.
3. **Extraction** – The cleaned text of the whole document is sent to a locally hosted LLM (**`qwen3.5:4b`** via Ollama, temperature 0). The prompt asks for exactly the six fields as one JSON object, with output-format instructions (e.g. dates as `DD.MM.YYYY`, value as a plain number, names without honorifics).
4. **Evaluation** – Each predicted field is compared with the ground truth in `test.csv` using exact-match, and per-field Recall is reported.

The extracted values are produced entirely by the language model from the document content. No regular expressions, fixed positions, static conditions or document-specific templates are used to determine field values.

### About the spaCy/NER training pipeline

`train_pipeline.py` converts the training documents into labelled examples (metadata values are located in the text with fuzzy matching) and trains a spaCy NER model in `artifacts/ner_model/`. This was an earlier experiment; with only 10 training documents it was not reliable, so **the trained NER model is not used for final inference**. Prediction and the API use Ollama only. Running the training pipeline is not required to reproduce the predictions.

## Project Structure

```text
data-extraction-from-documents/
├── assignment-1/
│   ├── data/
│   │   ├── train/            # training documents
│   │   ├── test/             # test documents
│   │   ├── train.csv
│   │   └── test.csv
│   └── assignment-details.pdf
├── configs/
│   └── extraction_fields.json   # the six fields and CSV column names
├── pipeline/
│   ├── document_loader.py    # DOCX reading / dispatch to OCR
│   ├── image_reader.py       # Tesseract OCR
│   ├── text_cleaner.py       # text normalisation
│   ├── annotation_builder.py # (training only) label spans for NER
│   └── dataset_writer.py     # (training only) spaCy dataset files
├── model/
│   ├── ollama_extractor.py   # LLM prompt + Ollama call (final inference)
│   ├── predictor.py          # predictor used by the script and the API
│   ├── ner_trainer.py        # (training only) spaCy NER experiment
│   └── model_utils.py
├── evaluation/
│   ├── metrics.py            # exact-match, per-field Recall / Precision / F1
│   └── evaluate_predictions.py
├── service/
│   └── api.py                # FastAPI service
├── tests/
├── artifacts/                # prepared training/test examples
├── outputs/                  # predictions.csv, evaluation_report.json
├── predict_documents.py
├── train_pipeline.py
├── inspect_dataset.py        # prints the CSV columns and row counts
└── requirements.txt
```

## Setup

All commands are run from the repository root.

### 1. Python environment

Requires Python 3.12.

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Tesseract OCR (for image documents)

```bash
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr
```

On Windows, install it from https://github.com/UB-Mannheim/tesseract/wiki and add it to `PATH`.

Verify:

```bash
tesseract --version
```

### 3. Ollama and the model

Install Ollama from https://ollama.com/download (macOS: `brew install ollama`), then start the server and download the model:

```bash
ollama serve                 # skip if the Ollama desktop app is already running
ollama pull qwen3.5:4b
ollama list                  # qwen3.5:4b should be listed
```

The model and server address can be changed with environment variables (defaults shown; see `.env.example`):

```bash
export OLLAMA_MODEL=qwen3.5:4b
export OLLAMA_HOST=http://localhost:11434
```

The results below were produced with `qwen3.5:4b` on Ollama 0.40.0.

## Dataset

```text
assignment-1/data/train/    assignment-1/data/train.csv    (10 documents)
assignment-1/data/test/     assignment-1/data/test.csv     (4 documents)
```

The test documents and `test.csv` are used for prediction and evaluation.

## Prediction

Make sure Ollama is running, then:

```bash
python predict_documents.py
```

This reads every document listed in `test.csv`, extracts the six fields and writes `outputs/predictions.csv` with an `_expected` and `_predicted` column for each field. A document that cannot be read or processed is still written with empty predictions, so it counts as a miss.

## Evaluation

```bash
python -m evaluation.evaluate_predictions
```

For each field separately:

- **True** = the predicted value exactly matches the expected value.
- **False** = the value does not match, or was not extracted.
- **Recall = True / (True + False)**, computed over test rows with a non-empty expected value.

The only normalisation before comparison is whitespace: leading/trailing spaces are removed and repeated spaces are collapsed (several labels in the CSV contain stray spaces, e.g. `"Hanumaiah "`). Case, punctuation and characters must match exactly. Precision and F1 are also reported; Recall is the primary metric.

The report is written to `outputs/evaluation_report.json`.

## Results

Per-field exact-match Recall on the 4 provided test documents (`outputs/evaluation_report.json`):

| Field | Correct | Recall |
|---|---|---|
| Agreement Value | 4 / 4 | 1.00 |
| Agreement Start Date | 4 / 4 | 1.00 |
| Agreement End Date | 2 / 4 | 0.50 |
| Renewal Notice (Days) | 3 / 4 | 0.75 |
| Party One | 2 / 4 | 0.50 |
| Party Two | 1 / 4 | 0.25 |

Main errors: two end dates were not extracted, one renewal notice was not extracted, and several party names differ from the label in honorifics, letter case or punctuation (e.g. `Mrs. S.Sakunthala` vs `S.Sakunthala`, `Kapil Mehrotra` vs `KAPIL MEHROTRA`, `B.Kishore` vs `.B.Kishore`), which count as misses under exact match.

## REST API

Start the FastAPI service (Ollama must be running):

```bash
uvicorn service.api:app --reload
```

Interactive Swagger documentation: http://127.0.0.1:8000/docs

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service status |
| GET | `/fields` | The six fields extracted |
| POST | `/extract` | Upload a `.docx`, `.png`, `.jpg` or `.jpeg` file and get the six fields |

The API uses the same loading, OCR, cleaning and Ollama extraction as `predict_documents.py`.

Example:

```bash
curl -X POST http://127.0.0.1:8000/extract \
  -F "file=@assignment-1/data/test/24158401-Rental-Agreement.png"
```

```json
{
  "filename": "24158401-Rental-Agreement.png",
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

## Tests

```bash
python -m pytest
```

## Optional: training pipeline

```bash
python -m spacy download en_core_web_sm
python train_pipeline.py
```

Writes `artifacts/train_examples.json`, `artifacts/test_examples.json`, the spaCy `.spacy` files and `artifacts/ner_model/`. As noted above, this model is not used by prediction or the API.

## Technologies Used

- Python 3.12
- Ollama (`qwen3.5:4b`) – final extraction
- Tesseract OCR (pytesseract, Pillow) – scanned images
- python-docx – DOCX reading
- pandas – CSV handling and outputs
- FastAPI / Uvicorn – REST API
- spaCy, RapidFuzz – optional NER training experiment only
