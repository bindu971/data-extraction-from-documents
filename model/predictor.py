from pathlib import Path

from model.ollama_extractor import OllamaExtractor


class MetadataPredictor:
    def __init__(self, model_dir="artifacts/ner_model"):
        self.model_dir = Path(model_dir)
        self.extractor = OllamaExtractor()

    def predict_text(self, text: str) -> dict:
        return self.extractor.extract(text)
