"""Strict row-complete TSV output helpers."""
import csv


def write_entity_lists(path, column, values, expected_ids=None):
    expected = set(values) if expected_ids is None else set(expected_ids)
    if set(values) != expected:
        raise ValueError("Output IDs do not exactly match expected IDs")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["source1_entity_id", column])
        for entity_id in sorted(expected):
            writer.writerow([entity_id, ",".join(sorted(values[entity_id]))])
