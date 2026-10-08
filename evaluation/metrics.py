from collections import defaultdict


def normalize_for_compare(value):
    if value is None:
        return ""
    return " ".join(str(value).casefold().split()).strip()


def exact_match(expected, predicted):
    return normalize_for_compare(expected) == normalize_for_compare(predicted)


def field_metrics(rows, fields):
    report = {}

    for field in fields:
        tp = 0
        fp = 0
        fn = 0

        for row in rows:
            expected = row.get(f"{field}_expected", "")
            predicted = row.get(f"{field}_predicted", "")

            expected_present = bool(normalize_for_compare(expected))
            predicted_present = bool(normalize_for_compare(predicted))

            if expected_present and predicted_present:
                if exact_match(expected, predicted):
                    tp += 1
                else:
                    fn += 1
                    fp += 1
            elif expected_present:
                fn += 1
            elif predicted_present:
                fp += 1

        recall_denominator = tp + fn
        precision_denominator = tp + fp

        recall = tp / recall_denominator if recall_denominator else 0.0
        precision = tp / precision_denominator if precision_denominator else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0
        )

        report[field] = {
            "true_exact_matches": tp,
            "false_predictions": fp,
            "misses": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    return report
