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

if __name__ == "__main__": unittest.main()
