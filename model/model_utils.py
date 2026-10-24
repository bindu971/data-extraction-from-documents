from pathlib import Path
import json


CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "extraction_fields.json"


def load_field_config(path=CONFIG_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["fields"]


def output_name_to_label(config):
    return {item["output_name"]: item["label"] for item in config}


def label_to_output_name(config):
    return {item["label"]: item["output_name"] for item in config}
