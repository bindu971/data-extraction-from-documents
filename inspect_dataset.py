from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent
for name in ["train.csv", "test.csv"]:
    path = root / "assignment-1" / "data" / name
    if path.exists():
        df = pd.read_csv(path)
        print(f"\n{name}")
        print("Columns:")
        for col in df.columns:
            print(" -", repr(col))
        print("Rows:", len(df))
    else:
        print("Missing:", path)
