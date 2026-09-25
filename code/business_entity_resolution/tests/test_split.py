import unittest
from business_entity_resolution.split import assign_partitions, select_s1, stable_hash

class SplitTests(unittest.TestCase):
    def test_reproducible(self):
        self.assertEqual(stable_hash(1, "x", "S1-1"), stable_hash(1, "x", "S1-1"))
        ids = [f"S1-{i}" for i in range(100)]
        first = assign_partitions(ids, 20260925, 80, 10, 10)
        second = assign_partitions(reversed(ids), 20260925, 80, 10, 10)
        self.assertEqual(first, second)
        self.assertEqual(list(first.values()).count("fit"), 80)

    def test_selector_returns_rows(self):
        sample = [
            {"entity_id": f"S1-{country}-{index}", "country": country}
            for country in ("India", "US") for index in range(20)
        ]
        singletons = {row["entity_id"] for row in sample if int(row["entity_id"].rsplit("-", 1)[1]) % 2 == 0}
        chosen = select_s1(sample, singletons, 20260925, 2)
        self.assertEqual(len(chosen), 8)
        self.assertTrue(all(isinstance(row, dict) for row in chosen))

if __name__ == "__main__": unittest.main()
