import unittest
from business_entity_resolution.validation import leakage_counts, ownership

class ValidationTests(unittest.TestCase):
    def test_ownership(self): self.assertEqual(ownership({"S1-1":{"S2-1"}})["S2-1"], "S1-1")
    def test_validation_candidate_ignored(self):
        result = leakage_counts({"S1-fit":{"S2-val","S2-u"}}, {"S1-fit":"fit","S1-val":"holdout"}, {"S2-val":"S1-val"})
        self.assertEqual(result["ignored_validation_owned_candidates"], 1)
        self.assertEqual(result["validation_owned_labeled_negative"], 0)

if __name__ == "__main__": unittest.main()
