import tempfile
import unittest
from pathlib import Path

from business_entity_resolution.resource_limits import Guard
from business_entity_resolution.submission import DurableLog, bucket_for, join_partitions, signature


class SubmissionTests(unittest.TestCase):
    def test_signature_is_country_gated_and_requires_address(self):
        base = {"entity_id": "S1-1", "business_name": "Café & Co.", "business_address": "1 Main St", "country": "France"}
        self.assertTrue(signature(base).startswith("France\x1e"))
        self.assertEqual(signature({**base, "business_address": ""}), "")
        self.assertEqual(bucket_for(signature(base), 8), bucket_for(signature(base), 8))

    def test_join_preserves_empty_and_france_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); buckets = 2
            for prefix in ("s1", "s2", "s3"):
                for bucket in range(buckets):
                    (root / f"{prefix}_{bucket:03d}.tsv").write_text("", encoding="utf-8")
            france_key = "France\x1ecafe\x1e1 main st"
            india_key = "India\x1eother\x1e2 road"
            bucket = bucket_for(france_key, buckets)
            (root / f"s1_{bucket:03d}.tsv").write_text(f"{france_key}\tS1-F\n", encoding="utf-8")
            (root / f"s2_{bucket:03d}.tsv").write_text(f"{france_key}\tS2-F\n", encoding="utf-8")
            other = bucket_for(india_key, buckets)
            with (root / f"s1_{other:03d}.tsv").open("a", encoding="utf-8") as handle:
                handle.write(f"{india_key}\tS1-I\n")
            matching, candidate = root / "matching.tsv", root / "candidate.tsv"
            result = join_partitions(root, buckets, matching, candidate, Guard(1024**3, 60), DurableLog(root / "run.jsonl"))
            text = matching.read_text(encoding="utf-8")
            self.assertIn("S1-F\tS2-F", text)
            self.assertIn("S1-I\t\n", text)
            self.assertEqual(matching.read_text(encoding="utf-8").replace("matched_entity_ids", "candidate_entity_ids"), candidate.read_text(encoding="utf-8"))
            self.assertEqual(result["france_queries"], 1)


if __name__ == "__main__":
    unittest.main()
