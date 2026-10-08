from pathlib import Path
import pandas as pd

from pipeline.document_loader import load_document
from pipeline.text_cleaner import clean_text
from model.predictor import MetadataPredictor
from model.model_utils import load_field_config


ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "assignment-1" / "data"


def locate_column(df):
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

    columns = {
        str(c).strip().casefold(): c
        for c in df.columns
    }

    for alias in aliases:
        if alias.casefold() in columns:
            return columns[alias.casefold()]

    raise ValueError(
        f"No filename column found. Columns: {list(df.columns)}"
    )


def resolve_document(docs_dir, filename):
    path = docs_dir / filename

    if path.exists():
        return path

    candidate = docs_dir / Path(filename).name

    if candidate.exists():
        return candidate

    for extension in (
        ".docx",
        ".pdf.docx",
        ".png",
        ".jpg",
        ".jpeg",
    ):
        candidate = docs_dir / (
            f"{Path(filename).name}{extension}"
        )

        if candidate.exists():
            return candidate

    return None


def main():
    csv_path = DATASET / "test.csv"
    docs_dir = DATASET / "test"

    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    if not docs_dir.exists():
        raise FileNotFoundError(docs_dir)

    # Keep ground-truth values exactly as written in the CSV.
    df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    file_col = locate_column(df)

    predictor = MetadataPredictor()
    config = load_field_config()

    rows = []

    for _, row in df.iterrows():
        filename = str(row[file_col]).strip()

        path = resolve_document(docs_dir, filename)

        # A document that cannot be processed is still written with
        # empty predictions, so it counts as False in the evaluation.
        predicted_labels = {}

        if path is None:
            print(f"Missing document: {filename}")
        else:
            try:
                text = clean_text(load_document(path))
                predicted_labels = predictor.predict_text(text)
            except Exception as exc:
                print(f"Failed to process {filename}: {exc}")

        output = {"file": filename}

        for item in config:
            output_name = item["output_name"]
            label = item["label"]

            expected = ""

            for alias in item["aliases"] + [output_name]:
                matching = next(
                    (
                        c for c in df.columns
                        if str(c).strip().casefold()
                        == alias.casefold()
                    ),
                    None,
                )

                if matching:
                    expected = row[matching]
                    break

            output[f"{output_name}_expected"] = expected
            output[f"{output_name}_predicted"] = (
                predicted_labels.get(label, "")
            )

        rows.append(output)

        print(
            f"Predicted: {filename} | "
            f"entities={len(predicted_labels)}"
        )

    output_dir = ROOT / "outputs"
    output_dir.mkdir(exist_ok=True)

    pd.DataFrame(rows).to_csv(
        output_dir / "predictions.csv",
        index=False,
    )

    print()
    print("Saved outputs/predictions.csv")


if __name__ == "__main__":
    main()
