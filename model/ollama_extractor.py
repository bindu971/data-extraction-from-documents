import json
import os
import urllib.request


FIELDS = [
    "Agreement Value",
    "Agreement Start Date",
    "Agreement End Date",
    "Renewal Notice (Days)",
    "Party One",
    "Party Two",
]

LABELS = {
    "Agreement Value": "AGREEMENT_VALUE",
    "Agreement Start Date": "AGREEMENT_START_DATE",
    "Agreement End Date": "AGREEMENT_END_DATE",
    "Renewal Notice (Days)": "RENEWAL_NOTICE_DAYS",
    "Party One": "PARTY_ONE",
    "Party Two": "PARTY_TWO",
}


class OllamaExtractor:
    def __init__(
        self,
        model=None,
        host=None,
    ):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
        self.host = (
            host
            or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        ).rstrip("/")

    def extract(self, text: str) -> dict:

        prompt = f"""
Extract the following six metadata fields from the contract.

Fields:
{json.dumps(FIELDS, ensure_ascii=False)}

Rules:
- Return ONLY one valid JSON object.
- Use exactly the six keys listed above.
- Agreement Value: return only the numeric value. Do not include Rs, currency symbols, commas, or other text.
- Party One: return only the party's name. Do not include titles such as Mr., Mrs., Sri, Smt., address, father's name, designation, or other details.
- Party Two: return only the party's name. Do not include address or additional legal/company description.
- Dates: identify the complete date from the document and return it as DD.MM.YYYY, including leading zeros.
- Party One and Party Two: return only the core person or organization name. Remove honorifics such as Mr., Mrs., Ms., Sri, Smt., Dr., etc. Remove addresses, father's names, designations, representative details, and legal descriptions.
- Renewal Notice (Days): search the entire document carefully for any notice period related to termination, renewal, or vacating the premises. Return only the numeric number of days when the document states a notice period in days. For example, "60 days" must return "60", and "one month notice" should be interpreted as 30 days when the dataset represents monthly notice periods as days. Do not confuse advance rent or lease duration with the notice period.
- Party Two: return the party name exactly as written as the tenant/lessee party, while removing honorifics such as Mr., Mrs., Sri, SRI, Smt., etc. Preserve punctuation, initials, spacing, and periods that are part of the actual name. Do not include addresses, father's names, representatives, designations, or legal descriptions.
- If a field is not present, return an empty string.
- Do not include explanations, markdown, or additional keys.
- Extract the information from the document; do not invent information.
- For Renewal Notice (Days), return the notice duration in days when the document explicitly expresses the duration in days. If the document states the duration in months, preserve the stated duration rather than inventing a calendar-specific conversion.
- Preserve names and values faithfully.

Contract:
{text}
""".strip()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
            },
        }

        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.loads(response.read().decode("utf-8"))

        raw = data.get("response", "").strip()
        result = json.loads(raw)

        return {
            LABELS[field]: str(result.get(field, "")).strip()
            for field in FIELDS
        }
