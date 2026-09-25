"""Small in-memory Stage 3A blocker."""
from collections import Counter, defaultdict
from .normalize import blocking_keys


class Blocker:
    def __init__(self, max_posting):
        self.max_posting = max_posting
        self.postings = defaultdict(list)

    def add(self, row):
        for key in blocking_keys(row["business_name"], row["business_address"]):
            self.postings[(row["country"], key)].append(row["entity_id"])

    def finalize(self):
        for posting in self.postings.values():
            posting.sort()

    def candidates(self, row):
        hits = Counter()
        skipped = 0
        for key in sorted(blocking_keys(row["business_name"], row["business_address"])):
            posting = self.postings.get((row["country"], key), ())
            if len(posting) > self.max_posting:
                skipped += 1
            else:
                hits.update(posting)
        return sorted(hits, key=lambda item: (-hits[item], item)), dict(hits), skipped

    def stats(self):
        return {"keys": len(self.postings), "posting_rows": sum(map(len, self.postings.values()))}
