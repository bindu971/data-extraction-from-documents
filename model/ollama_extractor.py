import json
import os
import urllib.error
import urllib.request

from model.model_utils import load_field_config


DEFAULT_MODEL = "qwen3.5:4b-q4_K_M"

# The examples below are invented for illustration; they are not taken
# from the dataset.
NAME_RULES = """\
- Party names: return the person's or organisation's name only.
  1. Drop any honorific or title before the name: Mr., Mrs., Ms., Miss,
     Sri, Shri, Smt., Dr., Prof., M/s.
  2. Drop everything that describes the party rather than naming it:
     "S/o", "D/o", "W/o", "son of" and the father's/husband's name after it,
     age, address, occupation, and roles such as "the owner" or "Lessee".
  3. Copy the remaining name exactly as written in the document, keeping its
     spelling, letter case, initials and punctuation.
  Examples:
    "Mr. R.K. SHARMA S/o Late K. Sharma, aged 52" -> "R.K. SHARMA"
    "Smt. Anita Rao W/o Suresh Rao, residing at Pune" -> "Anita Rao"
    "Sri. P. Kumar & Mrs. L. Kumar" -> "P. Kumar & L. Kumar"
    "M/s. ACME TRADERS Pvt Ltd, represented by its director" -> "ACME TRADERS Pvt Ltd\""""


def build_prompt(fields: list[dict], text: str) -> str:
    definitions = "\n".join(
        f'- "{item["output_name"]}": {item["description"]}'
        for item in fields
    )

    return f"""You extract metadata from a rental/lease agreement.
Read the whole document and return one JSON object with these keys:

{definitions}

Rules:
{NAME_RULES}
- Base every value on the document. Do not invent information.
- If a value cannot be found in the document, return an empty string.

Document:
{text}"""


def build_schema(fields: list[dict]) -> dict:
    names = [item["output_name"] for item in fields]
    return {
        "type": "object",
        "properties": {name: {"type": "string"} for name in names},
        "required": names,
    }


class OllamaExtractor:
    def __init__(self, model=None, host=None):
        self.model = model or os.getenv("OLLAMA_MODEL", DEFAULT_MODEL)
        self.host = (
            host
            or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "600"))
        # Large enough for the longest documents; Ollama silently
        # truncates prompts that exceed the context window.
        self.num_ctx = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
        self.attempts = 2
        self.fields = load_field_config()

    def _generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            # The JSON schema makes Ollama return exactly the six keys.
            "format": build_schema(self.fields),
            "options": {
                "temperature": 0,
                "num_ctx": self.num_ctx,
            },
        }

        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data.get("response", "")

    def extract(self, text: str) -> dict:
        prompt = build_prompt(self.fields, text)

        error = None
        for _ in range(self.attempts):
            try:
                result = json.loads(self._generate(prompt))
                break
            except (json.JSONDecodeError, urllib.error.URLError, TimeoutError) as exc:
                error = exc
        else:
            raise RuntimeError(f"Ollama extraction failed: {error}")

        return {
            item["label"]: str(result.get(item["output_name"], "")).strip()
            for item in self.fields
        }
