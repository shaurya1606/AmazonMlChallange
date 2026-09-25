"""Streaming immutable TSV input."""
import csv

SOURCE_HEADER = ["entity_id", "business_name", "business_address", "country"]
GT_HEADER = ["source1_entity_id", "matched_entity_ids"]


def rows(path, header):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames != header:
            raise ValueError(f"Unexpected header in {path}: {reader.fieldnames!r}")
        for line_number, row in enumerate(reader, 2):
            if None in row:
                raise ValueError(f"Malformed row {line_number} in {path}")
            yield {key: (value or "") for key, value in row.items()}


def matches(raw):
    values = tuple(raw.split(",")) if raw.strip() else ()
    if len(values) != len(set(values)):
        raise ValueError("Duplicate ID in ground truth")
    return values
