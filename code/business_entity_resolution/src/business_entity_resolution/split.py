"""Deterministic Stage 3A sampling."""
import hashlib
import heapq
from collections import defaultdict

HASH_MAX = 1 << 256


def stable_hash(seed, namespace, value):
    payload = f"{seed}\0{namespace}\0{value}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest(), "big")


def is_safe_outer_train(value):
    return value >= int(HASH_MAX * 0.90)


def select_s1(source_rows, singleton_ids, seed, per_stratum):
    heaps = defaultdict(list)
    counts = defaultdict(lambda: [0, 0])
    cutoff = int(HASH_MAX * 0.90)
    for row in source_rows:
        entity_id = row["entity_id"]
        stratum = (row["country"], entity_id in singleton_ids)
        value = stable_hash(seed, "outer_s1", entity_id)
        counts[stratum][0] += 1
        counts[stratum][1] += value < cutoff
        item = (value, entity_id, row)
        heap = heaps[stratum]
        if len(heap) < per_stratum:
            heapq.heappush(heap, item)
        elif item[:2] > heap[0][:2]:
            heapq.heapreplace(heap, item)
    selected = []
    for stratum in sorted(heaps):
        if len(heaps[stratum]) != per_stratum:
            raise ValueError(f"Insufficient records in stratum {stratum}")
        if counts[stratum][1] < (counts[stratum][0] + 4) // 5:
            raise ValueError(f"Cannot prove outer-train membership for {stratum}")
        selected.extend(item[2] for item in sorted(heaps[stratum], reverse=True))
    return selected


def assign_partitions(ids, seed, fit, calibration, holdout):
    ordered = sorted(ids, key=lambda item: (stable_hash(seed, "pilot_partition", item), item))
    if len(ordered) != fit + calibration + holdout:
        raise ValueError("Partition sizes do not match")
    result = {item: "fit" for item in ordered[:fit]}
    result.update({item: "calibration" for item in ordered[fit:fit + calibration]})
    result.update({item: "holdout" for item in ordered[fit + calibration:]})
    return result


def take(values, seed, namespace, count):
    return sorted(set(values), key=lambda item: (stable_hash(seed, namespace, item), item))[:count]
