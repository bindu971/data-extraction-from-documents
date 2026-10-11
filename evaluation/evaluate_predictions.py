import argparse
import json
from pathlib import Path
import pandas as pd

from evaluation.metrics import field_metrics
from model.model_utils import load_field_config


def main():
    parser = argparse.ArgumentParser(description="Per-field exact-match evaluation.")
    parser.add_argument("--split", choices=["test", "train"], default="test")
    split = parser.parse_args().split

    suffix = "" if split == "test" else f"_{split}"
    prediction_file = Path(f"outputs/predictions{suffix}.csv")
    report_file = Path(f"outputs/evaluation_report{suffix}.json")

    if not prediction_file.exists():
        raise FileNotFoundError(
            f"Run python predict_documents.py --split {split} first."
        )

    # Read every value as text so numbers such as "60" are not
    # converted to floats ("60.0") when a column has empty cells.
    df = pd.read_csv(prediction_file, dtype=str, keep_default_na=False)
    config = load_field_config()

    fields = [item["output_name"] for item in config]
    rows = df.to_dict(orient="records")

    report = field_metrics(rows, fields)

    report_file.parent.mkdir(exist_ok=True)
    report_file.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nEvaluation")
    print("=" * 70)
    for field, values in report.items():
        print(
            f"{field}: "
            f"Precision={values['precision']:.3f} "
            f"Recall={values['recall']:.3f} "
            f"F1={values['f1']:.3f}"
        )

    print(f"\nSaved: {report_file}")


if __name__ == "__main__":
    main()
