import unittest
from business_entity_resolution.normalize import normalize, stripped

class NormalizeTests(unittest.TestCase):
    def test_normalize(self): self.assertEqual(normalize(" Café & CO. "), "café and co")
    def test_suffix(self): self.assertEqual(stripped("Example Private Limited"), "example")

if __name__ == "__main__": unittest.main()
