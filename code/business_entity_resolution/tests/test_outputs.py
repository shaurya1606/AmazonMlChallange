import csv
import tempfile
import unittest
from pathlib import Path

from business_entity_resolution.outputs import write_entity_lists


class OutputTests(unittest.TestCase):
    def test_france_empty_rows_are_preserved(self):
        values = {"S1-France": set(), "S1-India": {"S2-1"}}
        with tempfile.TemporaryDirectory() as directory:
            for column in ("candidate_entity_ids", "matched_entity_ids"):
                path = Path(directory) / f"{column}.tsv"
                write_entity_lists(path, column, values, values)
                with path.open(encoding="utf-8", newline="") as handle:
                    rows = {row["source1_entity_id"]: row[column] for row in csv.DictReader(handle, delimiter="\t")}
                self.assertIn("S1-France", rows)
                self.assertEqual(rows["S1-France"], "")

    def test_unknown_or_missing_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                write_entity_lists(Path(directory) / "bad.tsv", "matched_entity_ids", {"S1-France": set()}, {"S1-France", "S1-US"})


if __name__ == "__main__":
    unittest.main()
