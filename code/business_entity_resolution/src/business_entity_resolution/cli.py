"""Bounded Stage 3B rules pilot."""
import argparse
import csv
import heapq
import json
import os
import platform
import sys
from collections import defaultdict
from pathlib import Path

from .bloom import BloomFilter
from .blocking import Blocker
from .io import GT_HEADER, SOURCE_HEADER, matches, rows
from .metrics import choose_threshold, count_summary, macro_f05, retrieval_metrics
from .resource_limits import Guard
from .scoring import score
from .split import assign_partitions, is_safe_outer_train, select_s1, stable_hash, take
from .validation import leakage_counts, ownership


def guarded(iterable, guard, interval=100000):
    for index, item in enumerate(iterable, 1):
        if index % interval == 0:
            guard.check()
        yield item


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_lists(path, column, values):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["source1_entity_id", column])
        for entity_id in sorted(values):
            writer.writerow([entity_id, ",".join(sorted(values[entity_id]))])


def disk_bytes(*directories):
    return sum(item.stat().st_size for directory in directories for item in directory.rglob("*") if item.is_file())


def keep_smallest(heap, item, limit):
    if len(heap) < limit:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def run(config_path, memory_gib, runtime_minutes, threads):
    if threads != 1:
        raise ValueError("Stage 3B permits exactly one worker")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["stage"] != "b" or config["threads"] != 1:
        raise ValueError("Not the approved Stage B configuration")

    root = Path(__file__).resolve().parents[4]
    train = root / "dataset" / "train"
    paths = {"s1": train / "train_source1.tsv", "s2": train / "train_source2.tsv", "s3": train / "train_source3.tsv", "gt": train / "train_ground_truth.tsv"}
    artifact = root / "artifacts" / "pilot" / "stage_b"
    experiment = root / "experiments" / "runs" / "stage3b_rules_pilot"
    if artifact.exists() or experiment.exists():
        raise FileExistsError("Refusing to overwrite Stage 3B artifacts")
    guard = Guard(int(memory_gib * 1024**3), runtime_minutes * 60)
    seed = config["seed"]

    singletons = set()
    for row in guarded(rows(paths["gt"], GT_HEADER), guard):
        if not row["matched_entity_ids"].strip():
            singletons.add(row["source1_entity_id"])

    selected_rows = select_s1(guarded(rows(paths["s1"], SOURCE_HEADER), guard), singletons, seed, config["per_stratum"])
    selected = {row["entity_id"]: row for row in selected_rows}
    if len(selected) != config["s1_total"]:
        raise ValueError("Incorrect S1 sample size")
    partitions = assign_partitions(selected, seed, config["fit"], config["calibration"], config["holdout"])

    truth = {entity_id: set() for entity_id in selected}
    labeled = BloomFilter(config["bloom_bits"], config["bloom_hashes"])
    other_heaps = {"S2": [], "S3": []}
    for row in guarded(rows(paths["gt"], GT_HEADER), guard):
        owner = row["source1_entity_id"]
        target_ids = matches(row["matched_entity_ids"])
        if owner in selected:
            truth[owner].update(target_ids)
        safe_owner = owner not in selected and is_safe_outer_train(stable_hash(seed, "outer_s1", owner))
        for target in target_ids:
            labeled.add(target)
            if safe_owner and target[:2] in other_heaps:
                keep_smallest(other_heaps[target[:2]], (-stable_hash(seed, "other", target), target, owner), config["other_owned"])

    own_ids = set().union(*truth.values())
    other_owner_candidates = {target: owner for heap in other_heaps.values() for _, target, owner in heap if target not in own_ids}
    other_ids = take(other_owner_candidates, seed, "other_final", config["other_owned"])
    unmatched_needed = config["target_total"] - len(own_ids) - len(other_ids)
    positive_ids = own_ids | set(other_ids)
    targets = {}
    unmatched_heaps = defaultdict(list)
    for source in ("s2", "s3"):
        for row in guarded(rows(paths[source], SOURCE_HEADER), guard):
            entity_id = row["entity_id"]
            if entity_id in positive_ids:
                targets[entity_id] = row
            elif entity_id not in labeled:
                value = stable_hash(seed, "probe", entity_id)
                keep_smallest(unmatched_heaps[(source, row["country"])], (-value, entity_id, row), config["probe_per_bucket"])
    unmatched_records = {item[2]["entity_id"]: item[2] for heap in unmatched_heaps.values() for item in heap}
    unmatched_ids = take(unmatched_records, seed, "unmatched_final", unmatched_needed)
    targets.update({entity_id: unmatched_records[entity_id] for entity_id in unmatched_ids})
    final_ids = positive_ids | set(unmatched_ids)
    missing = final_ids - set(targets)
    if missing or not own_ids <= set(targets):
        raise ValueError(f"Missing {len(missing)} sampled targets")

    owners = {target: owner for target, owner in other_owner_candidates.items() if target in final_ids}
    owners.update(ownership(truth))

    blocker = Blocker(config["max_posting"])
    for index, row in enumerate(targets.values(), 1):
        blocker.add(row)
        if index % 1000 == 0: guard.check()
    blocker.finalize()
    country_counts = defaultdict(int)
    for row in targets.values(): country_counts[row["country"]] += 1

    candidates, scored = {}, {}
    skipped = comparisons = 0
    for query_id, query in selected.items():
        ids, hits, skipped_now = blocker.candidates(query)
        candidates[query_id] = set(ids); skipped += skipped_now
        scored[query_id] = [(target, score(query, targets[target], hits[target])) for target in ids]
        comparisons += country_counts[query["country"]]
        guard.check()

    calibration = sorted(item for item in selected if partitions[item] == "calibration")
    holdout = sorted(item for item in selected if partitions[item] == "holdout")
    threshold, calibration_score = choose_threshold(scored, truth, calibration)
    predictions = {item: {target for target, value in scored[item] if value >= threshold} for item in selected}
    holdout_score = macro_f05(truth, predictions, holdout)
    counts = [len(candidates[item]) for item in sorted(selected)]
    leakage = leakage_counts(candidates, partitions, owners)

    artifact.mkdir(parents=True)
    experiment.mkdir(parents=True)
    write_lists(artifact / "pilot_candidate_pairs.tsv", "candidate_entity_ids", candidates)
    write_lists(artifact / "pilot_matches.tsv", "matched_entity_ids", predictions)
    with (artifact / "selected_s1.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n"); writer.writerow(["source1_entity_id", "country", "singleton", "partition"])
        for item in sorted(selected): writer.writerow([item, selected[item]["country"], str(item in singletons).lower(), partitions[item]])
    with (artifact / "target_manifest.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n"); writer.writerow(["target_entity_id", "country", "role"])
        for item in sorted(targets): writer.writerow([item, targets[item]["country"], "selected_positive" if item in own_ids else "other_positive" if item in set(other_ids) else "unmatched"])

    stage_a_artifact = root / "artifacts" / "pilot" / "stage_a"
    comparison = {"stage_a_available": stage_a_artifact.exists()}
    if comparison["stage_a_available"]:
        with (stage_a_artifact / "selected_s1.tsv").open(encoding="utf-8", newline="") as handle:
            stage_a_selected = {row["source1_entity_id"] for row in csv.DictReader(handle, delimiter="\t")}
        with (stage_a_artifact / "target_manifest.tsv").open(encoding="utf-8", newline="") as handle:
            stage_a_positives = {row["target_entity_id"] for row in csv.DictReader(handle, delimiter="\t") if row["role"] == "selected_positive"}
        with (stage_a_artifact / "pilot_candidate_pairs.tsv").open(encoding="utf-8", newline="") as handle:
            stage_a_candidates = {row["source1_entity_id"]: set(filter(None, row["candidate_entity_ids"].split(","))) for row in csv.DictReader(handle, delimiter="\t")}
        missed_a = {(query, target) for query, values in truth.items() for target in values if target not in stage_a_candidates.get(query, set())}
        recovered = {(query, target) for query, target in missed_a if target in candidates[query]}
        lost = {(query, target) for query, values in truth.items() for target in values if target in stage_a_candidates.get(query, set()) and target not in candidates[query]}
        comparison.update({"selected_s1_identical": stage_a_selected == set(selected), "selected_positive_ids_identical": stage_a_positives == own_ids, "stage_a_missed_truth_links": len(missed_a), "recovered_stage_a_misses": len(recovered), "lost_stage_a_hits": len(lost)})

    resource = guard.report()
    metrics = {"status": "completed", "stage": "3B", "rules_only": True, "dataset_scan_passes": {"ground_truth": 2, "source1": 1, "source2": 1, "source3": 1, "total": 5}, "s1_count": len(selected), "target_count": len(targets), "target_roles": {"selected_positive": len(own_ids), "other_positive": len(other_ids), "unmatched": len(unmatched_ids)}, "partition_counts": {name: list(partitions.values()).count(name) for name in ("fit", "calibration", "holdout")}, "retrieval": retrieval_metrics(truth, candidates, sorted(selected)), "candidate_counts": count_summary(counts), "total_candidate_pairs": sum(counts), "sample_conditioned_reduction_ratio": 1 - sum(counts) / comparisons, "skipped_common_keys": skipped, "blocking_index": blocker.stats(), "labeled_filter": labeled.stats(), "stage_a_comparison": comparison, "threshold": threshold, "calibration_macro_f05": calibration_score, "holdout_macro_f05": holdout_score, "leakage": leakage, "resources": resource, "limits": {"threads": threads, "memory_gib": memory_gib, "runtime_minutes": runtime_minutes}}
    write_json(experiment / "manifest.json", {"config": config, "python": sys.version, "platform": platform.platform(), "thread_environment": {key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}, "inputs": {key: {"bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns} for key, path in paths.items()}})
    write_json(experiment / "stage_b_metrics.json", metrics)
    metrics["disk_bytes"] = disk_bytes(artifact, experiment)
    write_json(experiment / "stage_b_metrics.json", metrics)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


def main():
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True); pilot = sub.add_parser("pilot")
    pilot.add_argument("--config", type=Path, required=True); pilot.add_argument("--stage", choices=["b"], required=True); pilot.add_argument("--max-memory-gib", type=float, required=True); pilot.add_argument("--max-runtime-minutes", type=float, required=True); pilot.add_argument("--threads", type=int, required=True)
    args = parser.parse_args()
    return run(args.config.resolve(), args.max_memory_gib, args.max_runtime_minutes, args.threads)


if __name__ == "__main__":
    raise SystemExit(main())
