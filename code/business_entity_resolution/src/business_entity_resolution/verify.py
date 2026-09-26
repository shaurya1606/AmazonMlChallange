"""Independent low-memory verification for generated submission files."""
import csv
import itertools
import json
from pathlib import Path

from .io import SOURCE_HEADER, rows


def parse_ids(raw):
    values = raw.split(",") if raw else []
    if len(values) != len(set(values)):
        raise ValueError("Duplicate target ID in output row")
    return set(values)


def verify(root):
    matching_path = root / "output" / "matching_results.tsv"
    candidate_path = root / "output" / "candidate_pairs.tsv"
    expected_header = (["source1_entity_id", "matched_entity_ids"], ["source1_entity_id", "candidate_entity_ids"])
    output_ids = set(); referenced = set(); france_output = empty_rows = row_count = 0
    with matching_path.open(encoding="utf-8", newline="") as mh, candidate_path.open(encoding="utf-8", newline="") as ch:
        matching = csv.DictReader(mh, delimiter="\t"); candidate = csv.DictReader(ch, delimiter="\t")
        if matching.fieldnames != expected_header[0] or candidate.fieldnames != expected_header[1]:
            raise ValueError("Incorrect output header")
        for left, right in itertools.zip_longest(matching, candidate):
            if left is None or right is None or left["source1_entity_id"] != right["source1_entity_id"]:
                raise ValueError("Output row alignment differs")
            query_id = left["source1_entity_id"]
            if query_id in output_ids:
                raise ValueError(f"Duplicate output query ID: {query_id}")
            output_ids.add(query_id); row_count += 1
            matches = parse_ids(left["matched_entity_ids"]); candidates = parse_ids(right["candidate_entity_ids"])
            if not matches <= candidates:
                raise ValueError(f"Match outside candidates: {query_id}")
            if any(not value.startswith(("S2-", "S3-")) for value in candidates):
                raise ValueError(f"Invalid target prefix: {query_id}")
            referenced.update(candidates); empty_rows += not candidates

    expected_ids = set(); france_ids = set()
    for row in rows(root / "dataset/test/test_source1.tsv", SOURCE_HEADER):
        expected_ids.add(row["entity_id"])
        if row["country"] == "France":
            france_ids.add(row["entity_id"])
    if output_ids != expected_ids:
        raise ValueError(f"S1 coverage mismatch: missing={len(expected_ids-output_ids)}, extra={len(output_ids-expected_ids)}")
    france_output = len(france_ids & output_ids)

    missing_targets = set(referenced)
    for filename in ("test_source2.tsv", "test_source3.tsv"):
        for row in rows(root / "dataset/test" / filename, SOURCE_HEADER):
            missing_targets.discard(row["entity_id"])
    if missing_targets:
        raise ValueError(f"Unknown target IDs: {len(missing_targets)}")
    return {"status": "PASS", "rows": row_count, "empty_rows": empty_rows, "referenced_target_ids": len(referenced), "france_expected": len(france_ids), "france_output": france_output, "matches_subset_candidates": True, "unknown_target_ids": 0}


def main():
    root = Path(__file__).resolve().parents[4]
    print(json.dumps(verify(root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
