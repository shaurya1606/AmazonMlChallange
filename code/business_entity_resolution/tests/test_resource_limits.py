import unittest
from business_entity_resolution.resource_limits import Guard, rss

class ResourceTests(unittest.TestCase):
    def test_memory_query_and_guard(self):
        self.assertGreater(rss(), 0)
        guard = Guard(1024**3, 60)
        guard.check()
        self.assertGreater(guard.peak, 0)

if __name__ == "__main__": unittest.main()
