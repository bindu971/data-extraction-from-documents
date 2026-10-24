from model.ollama_extractor import OllamaExtractor


class MetadataPredictor:
    def __init__(self):
        self.extractor = OllamaExtractor()

    def predict_text(self, text: str) -> dict:
        return self.extractor.extract(text)
