"""Small standard-library Bloom filter used to exclude labeled targets."""
import hashlib


class BloomFilter:
    """Memory-bounded membership filter with false positives but no false negatives."""

    def __init__(self, bits=1 << 28, hashes=4):
        if bits <= 0 or hashes <= 0:
            raise ValueError("bits and hashes must be positive")
        self.bits = bits
        self.hashes = hashes
        self.data = bytearray((bits + 7) // 8)
        self.count = 0

    def _positions(self, value):
        digest = hashlib.blake2b(value.encode("utf-8"), digest_size=16).digest()
        first = int.from_bytes(digest[:8], "big")
        second = int.from_bytes(digest[8:], "big") | 1
        for index in range(self.hashes):
            yield (first + index * second) % self.bits

    def add(self, value):
        for position in self._positions(value):
            self.data[position >> 3] |= 1 << (position & 7)
        self.count += 1

    def __contains__(self, value):
        return all(self.data[position >> 3] & (1 << (position & 7)) for position in self._positions(value))

    def stats(self):
        return {"bits": self.bits, "bytes": len(self.data), "hashes": self.hashes, "items_added": self.count}
