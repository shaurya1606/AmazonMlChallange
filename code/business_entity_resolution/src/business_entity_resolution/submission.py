"""Disk-partitioned exact-signature baseline for complete local submission files."""
import csv
import hashlib
import json
import os
import platform
import shutil
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .io import SOURCE_HEADER, rows
from .normalize import normalize
from .resource_limits import Guard


class DurableLog:
    def __init__(self, path):
        self.path = path
        self.start = time.perf_counter()
        path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, phase, status, guard=None, **details):
        record = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": round(time.perf_counter() - self.start, 6), "phase": phase, "status": status, **details}
        if guard is not None:
            record["guard"] = {"status": "ok", **guard.report()}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush(); os.fsync(handle.fileno())


def signature(row):
    name = normalize(row["business_name"])
    address = normalize(row["business_address"])
    if not name or not address:
        return ""
    return "\x1e".join((row["country"], name, address))


def bucket_for(value, bucket_count):
    return int.from_bytes(hashlib.blake2b(value.encode("utf-8"), digest_size=8).digest(), "big") % bucket_count


def disk_bytes(path):
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file()) if path.exists() else 0


def partition_source(path, directory, prefix, bucket_count, guard, run_log, row_limit=None):
    handles = [(directory / f"{prefix}_{index:03d}.tsv").open("w", encoding="utf-8", newline="") for index in range(bucket_count)]
    counts = [0] * bucket_count
    skipped_empty = 0
    started = time.perf_counter()
    run_log.write(f"partition_{prefix}", "started", guard)
    try:
        for index, row in enumerate(rows(path, SOURCE_HEADER), 1):
            if index % 1000 == 0:
                guard.check()
            if row_limit is not None and index > row_limit:
                break
            key = signature(row)
            if not key:
                skipped_empty += 1
                if prefix == "s1":
                    key = "\x1e".join((row["country"], normalize(row["business_name"]), ""))
                else:
                    continue
            bucket = bucket_for(key, bucket_count)
            handles[bucket].write(f"{key}\t{row['entity_id']}\n")
            counts[bucket] += 1
    finally:
        for handle in handles:
            handle.close()
    total = sum(counts)
    run_log.write(f"partition_{prefix}", "completed", guard, rows_written=total, skipped_empty=skipped_empty, phase_seconds=round(time.perf_counter() - started, 6))
    return total, skipped_empty


def join_partitions(directory, bucket_count, matching_path, candidate_path, guard, run_log):
    total_queries = total_pairs = empty_queries = max_candidates = france_queries = 0
    with matching_path.open("w", encoding="utf-8", newline="") as matching, candidate_path.open("w", encoding="utf-8", newline="") as candidate:
        matching.write("source1_entity_id\tmatched_entity_ids\n")
        candidate.write("source1_entity_id\tcandidate_entity_ids\n")
        for bucket in range(bucket_count):
            started = time.perf_counter()
            target_map = defaultdict(list)
            for prefix in ("s2", "s3"):
                path = directory / f"{prefix}_{bucket:03d}.tsv"
                with path.open(encoding="utf-8", newline="") as handle:
                    for index, line in enumerate(handle, 1):
                        if index % 1000 == 0:
                            guard.check()
                        key, entity_id = line.rstrip("\r\n").rsplit("\t", 1)
                        target_map[key].append(entity_id)
            query_path = directory / f"s1_{bucket:03d}.tsv"
            bucket_queries = bucket_pairs = 0
            with query_path.open(encoding="utf-8", newline="") as handle:
                for index, line in enumerate(handle, 1):
                    if index % 1000 == 0:
                        guard.check()
                    key, entity_id = line.rstrip("\r\n").rsplit("\t", 1)
                    values = sorted(set(target_map.get(key, ())))
                    raw = ",".join(values)
                    matching.write(f"{entity_id}\t{raw}\n")
                    candidate.write(f"{entity_id}\t{raw}\n")
                    bucket_queries += 1; bucket_pairs += len(values)
                    empty_queries += not values
                    max_candidates = max(max_candidates, len(values))
                    france_queries += key.startswith("France\x1e")
            total_queries += bucket_queries; total_pairs += bucket_pairs
            run_log.write("join_bucket", "completed", guard, bucket=bucket, queries=bucket_queries, candidate_pairs=bucket_pairs, phase_seconds=round(time.perf_counter() - started, 6))
    return {"queries": total_queries, "candidate_pairs": total_pairs, "empty_queries": empty_queries, "max_candidates_per_query": max_candidates, "france_queries": france_queries}


def run(config_path, mode, row_limit=None):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parents[4]
    test = root / "dataset" / "test"
    paths = {"s1": test / "test_source1.tsv", "s2": test / "test_source2.tsv", "s3": test / "test_source3.tsv"}
    name = "submission_exact_smoke" if mode == "smoke" else "submission_exact_v1"
    run_dir = root / "experiments" / "runs" / name
    partition_dir = root / "artifacts" / "submission_exact" / name / "partitions"
    output_dir = root / ("artifacts/pilot/submission_exact_smoke" if mode == "smoke" else "output")
    if run_dir.exists() or partition_dir.parent.exists() or output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite existing {name} paths")
    free_disk = shutil.disk_usage(root).free
    if free_disk < config["min_free_disk_gib"] * 1024**3:
        raise RuntimeError("Insufficient free disk")
    partition_dir.mkdir(parents=True)
    output_dir.mkdir(parents=True)
    run_log = DurableLog(run_dir / "run.jsonl")
    guard = Guard(int(config["max_memory_gib"] * 1024**3), config["max_runtime_hours"] * 3600)
    run_log.write("run", "started", guard, mode=mode, row_limit=row_limit, free_disk_bytes=free_disk)
    manifest = {"status": "running", "mode": mode, "config": config, "python": sys.version, "platform": platform.platform(), "inputs": {key: {"bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns} for key, path in paths.items()}}
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    try:
        source_counts = {}
        skipped = {}
        for key in ("s1", "s2", "s3"):
            source_counts[key], skipped[key] = partition_source(paths[key], partition_dir, key, config["bucket_count"], guard, run_log, row_limit)
        matching = output_dir / ("pilot_matching_results.tsv" if mode == "smoke" else "matching_results.tsv")
        candidate = output_dir / ("pilot_candidate_pairs.tsv" if mode == "smoke" else "candidate_pairs.tsv")
        joined = join_partitions(partition_dir, config["bucket_count"], matching, candidate, guard, run_log)
        metrics = {"status": "completed", "mode": mode, "strategy": "exact normalized country+name+address", "source_rows": source_counts, "skipped_empty_signature_targets": skipped, "join": joined, "resources": guard.report(), "partition_bytes": disk_bytes(partition_dir), "output_bytes": matching.stat().st_size + candidate.stat().st_size, "limitations": "Precision-first exact signature baseline; noisy name/address variants are intentionally missed."}
        (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest["status"] = "completed"
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        run_log.write("run", "finished", guard, exit_status="success", exit_code=0)
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0
    except BaseException as error:
        run_log.write("run", "finished", exit_status="failed", exit_code=1, error_type=type(error).__name__, error=str(error))
        raise
