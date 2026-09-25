import unittest
from business_entity_resolution.blocking import Blocker

class BlockingTests(unittest.TestCase):
    def test_country_gate(self):
        blocker = Blocker(10)
        blocker.add({"entity_id":"S2-1","business_name":"Acme Ltd","business_address":"1 Road","country":"US"})
        blocker.add({"entity_id":"S3-1","business_name":"Acme Ltd","business_address":"1 Road","country":"India"})
        blocker.finalize()
        ids, _, _ = blocker.candidates({"entity_id":"S1-1","business_name":"ACME LIMITED","business_address":"1 Road","country":"US"})
        self.assertIn("S2-1", ids); self.assertNotIn("S3-1", ids)

    def test_text_address_recovers_changed_name(self):
        blocker = Blocker(10)
        blocker.add({"entity_id":"S2-1","business_name":"Northwind Trading","business_address":"17 Merchant Avenue","country":"US"})
        blocker.finalize()
        ids, hits, _ = blocker.candidates({"entity_id":"S1-1","business_name":"Completely Different","business_address":"Merchant Avenue","country":"US"})
        self.assertIn("S2-1", ids)
        self.assertGreaterEqual(hits["S2-1"], 2)

if __name__ == "__main__": unittest.main()
