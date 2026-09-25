import unittest

from business_entity_resolution.bloom import BloomFilter


class BloomFilterTests(unittest.TestCase):
    def test_added_values_are_never_missing(self):
        bloom = BloomFilter(bits=1024, hashes=3)
        values = [f"S2-{index}" for index in range(100)]
        for value in values:
            bloom.add(value)
        self.assertTrue(all(value in bloom for value in values))

    def test_invalid_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            BloomFilter(bits=0)


if __name__ == "__main__":
    unittest.main()
