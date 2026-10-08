from pathlib import Path
import random
import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding


def train_ner(
    spacy_data_path: str,
    output_dir: str = "artifacts/ner_model",
    iterations: int = 25,
    dropout: float = 0.25,
):
    nlp = spacy.load("en_core_web_sm")
    ner = nlp.get_pipe("ner")

    docs = list(spacy.tokens.DocBin().from_disk(spacy_data_path).get_docs(nlp.vocab))
    labels = sorted({ent.label_ for doc in docs for ent in doc.ents})

    for label in labels:
        ner.add_label(label)

    examples = [Example.from_dict(doc, {"entities": [(e.start_char, e.end_char, e.label_) for e in doc.ents]})
                for doc in docs]

    optimizer = nlp.initialize(get_examples=lambda: examples)

    for epoch in range(iterations):
        random.shuffle(examples)
        losses = {}

        batches = minibatch(examples, size=compounding(2.0, 8.0, 1.5))
        for batch in batches:
            nlp.update(batch, drop=dropout, sgd=optimizer, losses=losses)

        print(f"epoch={epoch + 1:02d} losses={losses}")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output)
    return output
