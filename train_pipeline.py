from pathlib import Path

import pandas as pd

from pipeline.document_loader import load_document
from pipeline.text_cleaner import clean_text, clean_value
from pipeline.dataset_writer import write_json, make_spacy_file
from model.model_utils import load_field_config
from model.ner_trainer import train_ner


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "assignment-1" / "data"
ARTIFACTS = ROOT / "artifacts"


def locate_column(df, aliases):
    """Find a CSV column using case-insensitive aliases."""
    normalized = {
        str(column).strip().casefold(): column
        for column in df.columns
    }

    for alias in aliases:
        key = alias.strip().casefold()
        if key in normalized:
            return normalized[key]

    return None


def build_field_columns(df, config):
    """Map configured output fields to the actual CSV columns."""
    result = {}

    for item in config:
        aliases = item.get("aliases", []) + [item["output_name"]]
        column = locate_column(df, aliases)

        if column is None:
            print(
                f"Warning: no CSV column found for "
                f"{item['output_name']}"
            )
        else:
            result[item["output_name"]] = column

    return result


def filename_column(df):
    """Identify the document filename column."""
    aliases = [
        "filename",
        "file_name",
        "file name",
        "document",
        "document_name",
        "document_id",
        "file",
        "id",
    ]

    return locate_column(df, aliases)


def process_split(
    csv_path,
    docs_dir,
    output_json,
    output_spacy,
    config,
):
    """Convert a labeled CSV split into training examples."""
    df = pd.read_csv(csv_path).fillna("")

    file_col = filename_column(df)

    if file_col is None:
        raise ValueError(
            f"Could not identify the document filename column "
            f"in {csv_path}. Columns found: {list(df.columns)}"
        )

    field_columns = build_field_columns(df, config)

    output_to_label = {
        item["output_name"]: item["label"]
        for item in config
    }

    records = []

    for _, row in df.iterrows():
        filename = str(row[file_col]).strip()

        if not filename:
            print("Skipping row with empty filename.")
            continue

        path = docs_dir / filename

        # Fall back to the basename if the CSV contains a path.
        if not path.exists():
            candidate = docs_dir / Path(filename).name

            if candidate.exists():
                path = candidate
            else:
                # CSV filenames may omit the document extension.
                path = None

                for extension in (".docx", ".pdf.docx", ".png", ".jpg", ".jpeg"):
                    candidate = docs_dir / (
                        f"{Path(filename).name}{extension}"
                    )

                    if candidate.exists():
                        path = candidate
                        break

                if path is None:
                    print(f"Skipping missing document: {filename}")
                    continue

        try:
            raw_text = load_document(path)
            text = clean_text(raw_text)
        except Exception as exc:
            print(f"Failed to read {filename}: {exc}")
            continue

        if not text.strip():
            print(f"Skipping empty document: {filename}")
            continue

        labels = {}

        for output_name, source_column in field_columns.items():
            value = clean_value(row[source_column])

            if not value:
                continue

            internal_label = output_to_label[output_name]
            labels[internal_label] = value

        records.append(
            {
                "file": filename,
                "text": text,
                "labels": labels,
            }
        )

        print(
            f"Prepared: {filename} | "
            f"fields={len(labels)} | "
            f"characters={len(text)}"
        )

    write_json(records, output_json)
    make_spacy_file(records, output_spacy)

    print()
    print(
        f"Prepared {len(records)} examples -> "
        f"{output_json}"
    )


def main():
    ARTIFACTS.mkdir(parents=True, exist_ok=True)

    config = load_field_config()

    train_csv = DATASET / "train.csv"
    train_docs = DATASET / "train"

    if not train_csv.exists():
        raise FileNotFoundError(
            f"Training CSV not found: {train_csv}"
        )

    if not train_docs.exists():
        raise FileNotFoundError(
            f"Training documents directory not found: {train_docs}"
        )

    process_split(
        train_csv,
        train_docs,
        ARTIFACTS / "train_examples.json",
        ARTIFACTS / "train.spacy",
        config,
    )

    test_csv = DATASET / "test.csv"
    test_docs = DATASET / "test"

    if test_csv.exists() and test_docs.exists():
        process_split(
            test_csv,
            test_docs,
            ARTIFACTS / "test_examples.json",
            ARTIFACTS / "test.spacy",
            config,
        )

    train_ner(
        str(ARTIFACTS / "train.spacy"),
        str(ARTIFACTS / "ner_model"),
    )


if __name__ == "__main__":
    main()
