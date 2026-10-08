from pathlib import Path
import os
from PIL import Image
import pytesseract


def ocr_image(path: str | Path) -> str:
    image = Image.open(path)
    language = os.getenv("OCR_LANGUAGE", "eng")
    text = pytesseract.image_to_string(image, lang=language)
    return text.strip()
