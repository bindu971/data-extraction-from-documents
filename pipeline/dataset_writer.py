import json
from pathlib import Path
import spacy
from spacy.tokens import DocBin

from pipeline.annotation_builder import build_spans, remove_overlaps
from pipeline.text_cleaner import clean_text, clean_value


def write_json(records, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


def make_spacy_file(records, path: Path):
    nlp = spacy.blank("en")
    doc_bin = DocBin(store_user_data=True)

    for record in records:
        text = record["text"]
        doc = nlp.make_doc(text)
        spans = build_spans(text, record["labels"])
        spans = remove_overlaps(spans)

        entities = []
        for span in spans:
            entity = doc.char_span(span.start, span.end, label=span.label, alignment_mode="contract")
            if entity is not None:
                entities.append(entity)

        doc.ents = entities
        doc_bin.add(doc)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc_bin.to_disk(path)


def prepare_records(rows, document_map, field_map):
    records = []
    unmatched = []

    for row in rows:
        filename = document_map(row)
        text = clean_text(document_map.document_text(filename))

        labels = {}
        for source_column, target_label in field_map.items():
            value = clean_value(row.get(source_column, ""))
            if value:
                labels[target_label] = value

        if text:
            records.append({
                "file": filename,
                "text": text,
                "labels": labels
            })

    return records, unmatched
