from dataclasses import dataclass
from rapidfuzz import fuzz


@dataclass
class Span:
    start: int
    end: int
    label: str


def _candidate_windows(text: str, value: str):
    """
    Generate candidate character windows without regular expressions.
    Window size is based on the token count of the target value.
    """
    text_tokens = text.split()
    value_tokens = value.split()

    if not value_tokens or not text_tokens:
        return

    wanted = len(value_tokens)
    low = max(1, wanted - 2)
    high = wanted + 3

    positions = []
    cursor = 0
    for token in text_tokens:
        start = text.find(token, cursor)
        if start < 0:
            start = cursor
        positions.append((start, start + len(token)))
        cursor = start + len(token)

    for size in range(low, high + 1):
        for i in range(0, len(positions) - size + 1):
            start = positions[i][0]
            end = positions[i + size - 1][1]
            yield start, end, text[start:end]


def locate_value(text: str, value: str, threshold: int = 82):
    if not value:
        return None

    exact = text.casefold().find(value.casefold())
    if exact >= 0:
        return exact, exact + len(value), 100

    best = None
    for start, end, candidate in _candidate_windows(text, value):
        score = fuzz.token_set_ratio(candidate, value)
        if best is None or score > best[0]:
            best = (score, start, end)

    if best and best[0] >= threshold:
        return best[1], best[2], best[0]

    return None


def build_spans(text: str, values: dict[str, str]):
    spans = []

    for label, value in values.items():
        found = locate_value(text, value)
        if found:
            start, end, _ = found
            spans.append(Span(start, end, label))

    spans.sort(key=lambda item: (item.start, item.end))
    return spans


def remove_overlaps(spans: list[Span]) -> list[Span]:
    accepted = []
    occupied_until = -1

    for span in sorted(spans, key=lambda item: (item.start, -(item.end - item.start))):
        if span.start >= occupied_until:
            accepted.append(span)
            occupied_until = span.end

    return sorted(accepted, key=lambda item: item.start)
