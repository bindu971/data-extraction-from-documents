# AI/ML Document Metadata Extraction

An AI-powered document extraction pipeline that extracts six metadata fields from rental agreements in DOCX and scanned image formats using a local LLM and OCR.

**Key features**

- Extracts six fields: Agreement Value, Start Date, End Date, Renewal Notice, Party One, and Party Two.
- Uses Python, Tesseract OCR, and Ollama with a pretrained Qwen model.
- Supports DOCX, PNG, JPG, and JPEG files.
- Provides a FastAPI REST API for document uploads.
- Evaluates predictions using exact-match Precision, Recall, and F1-score.
- Includes automated tests for document loading, extraction logic, evaluation, and API endpoints.

The pipeline is designed to handle varying document layouts without relying on document-specific templates or fixed field positions.

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
3. **Extraction** – The cleaned text of the whole document is sent to a locally hosted LLM (**`qwen3.5:4b-q4_K_M`** via Ollama, temperature 0) in a single request:
   - The prompt is built from `configs/extraction_fields.json`, which defines each field by its _meaning_ (e.g. Party One = the owner/lessor, Renewal Notice = advance notice period in days with 1 month = 30 days, End Date = end of the lease term), plus general name rules (drop honorifics and "S/o …" clauses, keep the name exactly as written). The few name examples in the prompt are invented, not taken from the dataset.
   - A **JSON schema** is passed to Ollama (`format`), so the model's output is always a JSON object with exactly the six keys.
   - The context window is set explicitly (`num_ctx` = 8192) so long documents are not silently truncated; an invalid or failed response is retried once.
4. **Evaluation** – Each predicted field is compared with the ground truth using exact-match, and per-field Recall is reported.

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
│   └── extraction_fields.json   # the six fields: names, CSV columns, definitions used in the prompt
├── pipeline/
│   ├── document_loader.py    # DOCX reading / dispatch to OCR
│   ├── image_reader.py       # Tesseract OCR
│   ├── text_cleaner.py       # text normalisation
│   ├── annotation_builder.py # (training only) label spans for NER
│   └── dataset_writer.py     # (training only) spaCy dataset files
├── model/
│   ├── ollama_extractor.py   # prompt + JSON schema + Ollama call (final inference)
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
├── outputs/                  # predictions and evaluation reports (test and train splits)
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
ollama serve                       # skip if the Ollama app/service is already running
ollama pull qwen3.5:4b-q4_K_M      # about 3.3 GB
ollama list                        # qwen3.5:4b-q4_K_M should be listed
```

The exact quantisation is pinned because it matters: on an Apple M2, Ollama had also installed an MLX/NVFP4 build under the `qwen3.5:4b` name, which took about 85 s per request before generating anything (about 2 s with `q4_K_M`) and reported structured (JSON-schema) output as unavailable. The `q4_K_M` build runs on every platform Ollama supports.

Optional settings (defaults shown; see `.env.example`):

```bash
export OLLAMA_MODEL=qwen3.5:4b-q4_K_M
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_NUM_CTX=8192     # context window in tokens
export OLLAMA_TIMEOUT=600      # seconds per request
```

The results below were produced with `qwen3.5:4b-q4_K_M` on Ollama 0.40.0 (Apple M2, 8 GB RAM; roughly 10–60 s per document on that machine).

## Dataset

```text
assignment-1/data/train/    assignment-1/data/train.csv    (10 rows, 9 documents present)
assignment-1/data/test/     assignment-1/data/test.csv     (4 rows, 4 documents)
```

- **test** is the evaluation set; its results are the reported results.
- **train** is used as a development set: prompt and design changes were checked on it, so that the test set was not used for tuning. The model itself is not fine-tuned.

Notes on the provided data (left unchanged; they affect the train-split scores only):

- `24158401-Rental-Agreement` is listed in `train.csv` but its file is only in `test/`, so on the train split it is always counted as missed.
- The `train.csv` rows for `54770958-Rental-Agreement` and `54945838-Rental-Agreement` appear to be swapped: the party names and rent of each row appear in the other document.
- Several train end-date labels are not real calendar dates (`31.11.2009`, `31.04.2011`, `31.02.2011`).

## Prediction

Make sure Ollama is running, then:

```bash
python predict_documents.py                 # test set  -> outputs/predictions.csv
python predict_documents.py --split train   # dev set   -> outputs/predictions_train.csv
```

This reads every document listed in the split's CSV, extracts the six fields and writes a CSV with an `_expected` and `_predicted` column for each field. A document that is missing or cannot be processed is still written with empty predictions, so it counts as a miss.

## Evaluation

```bash
python -m evaluation.evaluate_predictions                 # -> outputs/evaluation_report.json
python -m evaluation.evaluate_predictions --split train   # -> outputs/evaluation_report_train.json
```

For each field separately:

- **True** = the predicted value exactly matches the expected value.
- **False** = the value does not match, or was not extracted.
- **Recall = True / (True + False)**, computed over rows with a non-empty expected value.

The only normalisation before comparison is whitespace: leading/trailing spaces are removed and repeated spaces are collapsed (several labels in the CSV contain stray spaces, e.g. `"Hanumaiah "`). Case, punctuation and characters must match exactly. Precision and F1 are also reported; Recall is the primary metric.

## Results

Per-field exact-match Recall on the **4 provided test documents** (`outputs/evaluation_report.json`), produced by `python predict_documents.py` and `python -m evaluation.evaluate_predictions` with `qwen3.5:4b-q4_K_M`:
**Evaluation limitation:** The test set contains only four documents. These results provide an initial assessment of the extraction pipeline and should not be interpreted as a guarantee of performance on unseen documents. Party-name variations and date calculations remain areas for improvement.

| Field                 | Correct | Recall   |
| --------------------- | ------- | -------- |
| Agreement Value       | 4 / 4   | **1.00** |
| Agreement Start Date  | 4 / 4   | **1.00** |
| Agreement End Date    | 3 / 4   | **0.75** |
| Renewal Notice (Days) | 4 / 4   | **1.00** |
| Party One             | 4 / 4   | **1.00** |
| Party Two             | 1 / 4   | **0.25** |

Remaining test errors:

- End date of `95980236`: the document gives a duration, and the model computed `31.02.2011` instead of `31.03.2011`.
- Party Two: `V.V Ravi Kian` vs `V.V.Ravi Kian`; `SRI VYSHNAVI DAIRY SPECIALITIES Private Ltd.` vs `VYSHNAVI DAIRY SPECIALITIES Private Ltd`; `B.Kishore` vs the label `.B.Kishore`. Each counts as a miss under exact match.

With temperature 0 the output is deterministic: a repeated run produced identical predictions on both splits.

### How the results changed

Each step was evaluated on both splits; the decision to keep a change was based on the train (development) split. Columns are test Recall per field.

| Change                                                        | Value | Start | End  | Notice | Party One | Party Two | Test mean | Train mean |
| ------------------------------------------------------------- | ----- | ----- | ---- | ------ | --------- | --------- | --------- | ---------- |
| Initial submission (MLX/NVFP4 build, original prompt)         | 1.00  | 1.00  | 0.50 | 0.75   | 0.50      | 0.25      | **0.67**  | –          |
| 1. Pinned `q4_K_M` build (same prompt)                        | 1.00  | 0.75  | 0.50 | 0.75   | 0.75      | 0.25      | **0.67**  | 0.32       |
| 2. JSON schema, `num_ctx`, retry, field definitions in config | 1.00  | 1.00  | 0.75 | 0.75   | 0.25      | 0.00      | **0.62**  | 0.34       |
| 3. Clearer name rules with invented examples (final)          | 1.00  | 1.00  | 0.75 | 1.00   | 1.00      | 0.25      | **0.83**  | 0.46       |

Tried and not kept: OCR image preprocessing (grayscale, 2× upscaling, auto-contrast, `--psm 6`) found no additional label values in the training images; Qwen's "thinking" mode took about 14 minutes for one document on the test machine and returned no answer.

### Development (train) split

`outputs/evaluation_report_train.json`. Lower than the test scores mainly because of the data issues listed under _Dataset_ (one missing document, two swapped rows, invalid end-date labels) and the noisier OCR of some training documents.

| Field                 | Correct | Recall |
| --------------------- | ------- | ------ |
| Agreement Value       | 6 / 10  | 0.60   |
| Agreement Start Date  | 6 / 10  | 0.60   |
| Agreement End Date    | 3 / 10  | 0.30   |
| Renewal Notice (Days) | 4 / 9   | 0.44   |
| Party One             | 3 / 10  | 0.30   |
| Party Two             | 5 / 10  | 0.50   |

## REST API

Start the FastAPI service (Ollama must be running):

```bash
uvicorn service.api:app --reload
```

Interactive Swagger documentation: http://127.0.0.1:8000/docs

| Method | Endpoint   | Description                                                             |
| ------ | ---------- | ----------------------------------------------------------------------- |
| GET    | `/health`  | Service status                                                          |
| GET    | `/fields`  | The six fields extracted                                                |
| POST   | `/extract` | Upload a `.docx`, `.png`, `.jpg` or `.jpeg` file and get the six fields |

The API uses the same loading, OCR, cleaning and Ollama extraction as `predict_documents.py`. Errors: `400` unsupported file type, `422` no text could be read, `502` the Ollama request failed (e.g. Ollama not running).

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

The tests cover text cleaning, the evaluation metric, document loading, the prompt/JSON-schema construction and retry logic of the extractor, and the API endpoints. The Ollama call is replaced by a stub, so the tests run without Ollama.

## Optional: training pipeline

```bash
python -m spacy download en_core_web_sm
python train_pipeline.py
```

Writes `artifacts/train_examples.json`, `artifacts/test_examples.json`, the spaCy `.spacy` files and `artifacts/ner_model/`. As noted above, this model is not used by prediction or the API.

## Technologies Used

- Python 3.12
- Ollama (`qwen3.5:4b-q4_K_M`) – final extraction
- Tesseract OCR (pytesseract, Pillow) – scanned images
- python-docx – DOCX reading
- pandas – CSV handling and outputs
- FastAPI / Uvicorn – REST API
- spaCy, RapidFuzz – optional NER training experiment only
