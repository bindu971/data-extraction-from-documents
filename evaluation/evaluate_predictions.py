import json
from pathlib import Path
import pandas as pd

from evaluation.metrics import field_metrics
from model.model_utils import load_field_config


def main():
    prediction_file = Path("outputs/predictions.csv")
    if not prediction_file.exists():
        raise FileNotFoundError("Run python predict_documents.py first.")

    df = pd.read_csv(prediction_file).fillna("")
    config = load_field_config()

    fields = [item["output_name"] for item in config]
    rows = df.to_dict(orient="records")

    report = field_metrics(rows, fields)

    Path("outputs").mkdir(exist_ok=True)
    Path("outputs/evaluation_report.json").write_text(
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

    print("\nSaved: outputs/evaluation_report.json")


if __name__ == "__main__":
    main()
