import unittest

from business_entity_resolution.verify import parse_ids


class VerifyTests(unittest.TestCase):
    def test_parse_ids_and_duplicates(self):
        self.assertEqual(parse_ids("S2-1,S3-2"), {"S2-1", "S3-2"})
        self.assertEqual(parse_ids(""), set())
        with self.assertRaises(ValueError):
            parse_ids("S2-1,S2-1")


if __name__ == "__main__":
    unittest.main()
