import unittest
from business_entity_resolution.metrics import entity_f05

class MetricTests(unittest.TestCase):
    def test_singletons(self):
        self.assertEqual(entity_f05(set(), set()), 1.0)
        self.assertEqual(entity_f05(set(), {"S2-1"}), 0.0)
    def test_empty_prediction(self): self.assertEqual(entity_f05({"S2-1"}, set()), 0.0)
    def test_supplied_example(self): self.assertAlmostEqual(entity_f05({"S2-1","S3-1"},{"S2-1","S2-2","S3-1"}), 5/7)

if __name__ == "__main__": unittest.main()
