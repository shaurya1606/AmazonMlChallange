"""Bounded Stage 3C1d full-pool probe for ten validation queries."""
import csv
import json
import os
import platform
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .io import GT_HEADER, SOURCE_HEADER, matches, rows
from .metrics import count_summary, retrieval_metrics
from .normalize import SUFFIXES, blocking_keys, normalize
from .outputs import write_entity_lists
from .resource_limits import Guard
from .split import stable_hash


class RunLog:
    """Append-only phase log; a run is successful only with a final success event."""

    def __init__(self, path):
        self.path = path
        self.start = time.perf_counter()
        path.parent.mkdir(parents=True, exist_ok=True)

    def event(self, phase, status, guard=None, **details):
        record = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.perf_counter() - self.start, 6),
            "phase": phase,
            "status": status,
            **details,
        }
        if guard is not None:
            try:
                record["guard"] = {"status": "ok", **guard.report()}
            except RuntimeError as error:
                record["guard"] = {"status": "failed", "error": str(error)}
                self._write(record)
                raise
        self._write(record)

    def _write(self, record):
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def check_deadline(work_deadline):
    if time.perf_counter() >= work_deadline:
        raise RuntimeError("Stage 3C1d work deadline reached")


def guarded(iterable, guard, work_deadline, interval=1000):
    for index, item in enumerate(iterable, 1):
        check_deadline(work_deadline)
        if index % interval == 0:
            guard.check()
        yield item


def cheap_blocking_keys(name, address):
    """Return non-SimHash keys without repeating normalization work."""
    name_norm = normalize(name)
    name_tokens = tuple(name_norm.split())
    address_tokens = tuple(normalize(address).split())
    result = set()
    if name_norm:
        result.update((f"ne:{name_norm}", f"ns:{' '.join(sorted(name_tokens))}"))
    legal = " ".join(token for token in name_tokens if token not in SUFFIXES)
    if legal:
        result.add(f"nl:{legal}")
    for token in name_tokens:
        if len(token) >= 5:
            result.update((f"nt:{token}", f"np:{token[:4]}"))
    for token in address_tokens:
        if token.isdigit() and len(token) >= 3:
            result.add(f"ad:{token}")
        elif len(token) >= 5:
            result.update((f"at:{token}", f"ap:{token[:4]}"))
    return result


def key_family(key):
    if key.startswith(("ne:", "ns:", "nl:", "nt:", "np:")):
        return "name"
    if key.startswith(("ad:", "at:", "ap:")):
        return "address"
    return None


def family_rescue_queries(country, matched_keys, consumers):
    evidence = defaultdict(set)
    for key in matched_keys:
        family = key_family(key)
        if family is None:
            continue
        for query_id in consumers.get((country, key), ()):
            evidence[query_id].add(family)
    return {query_id: families for query_id, families in evidence.items() if {"name", "address"} <= families}


def assemble_candidates(queries, consumers, counts, postings, rescued, max_posting):
    candidates = {query_id: set(rescued.get(query_id, ())) for query_id in queries}
    skipped = 0
    for lookup, query_ids in consumers.items():
        if counts[lookup] > max_posting:
            skipped += len(query_ids)
            continue
        for row in postings[lookup]:
            for query_id in query_ids:
                candidates[query_id].add(row["entity_id"])
    return candidates, skipped


def enforce_candidate_caps(candidates, rescued, max_candidates, max_rescued):
    for query_id in sorted(candidates):
        if len(rescued.get(query_id, ())) > max_rescued:
            raise RuntimeError(f"Rescue candidate limit exceeded: query={query_id}, count={len(rescued[query_id])}, limit={max_rescued}")
        if len(candidates[query_id]) > max_candidates:
            raise RuntimeError(f"Total candidate limit exceeded: query={query_id}, count={len(candidates[query_id])}, limit={max_candidates}")


def classify_truth_link(cheap_overlap, posting_counts, max_posting, simhash_overlap, retrieved):
    rare = sum(posting_counts[key] <= max_posting for key in cheap_overlap)
    capped = len(cheap_overlap) - rare
    if rare:
        classification = "rare_cheap_key"
    elif len(cheap_overlap) >= 2:
        classification = "multi_key_rescue"
    elif capped:
        classification = "all_cheap_keys_capped"
    elif simhash_overlap:
        classification = "simhash_only"
    else:
        classification = "no_existing_key_overlap"
    return {"retrieved": retrieved, "classification": classification, "cheap_overlap_count": len(cheap_overlap), "rare_cheap_key_count": rare, "capped_cheap_key_count": capped, "simhash_band_overlap_count": simhash_overlap}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def disk_bytes(*directories):
    return sum(item.stat().st_size for directory in directories for item in directory.rglob("*") if item.is_file())


def select_queries(metadata, truth, stage_a_candidates, seed, count):
    eligible = []
    for entity_id, item in metadata.items():
        if item["partition"] not in {"calibration", "holdout"} or item["country"] not in {"India", "US"}:
            continue
        missed = bool(truth[entity_id] - stage_a_candidates.get(entity_id, set()))
        eligible.append((entity_id, item, missed))

    chosen = []
    for country in ("India", "US"):
        for singleton in (True, False):
            group = [entry for entry in eligible if entry[1]["country"] == country and entry[1]["singleton"] == singleton]
            group.sort(key=lambda entry: (not entry[2], stable_hash(seed, "stage_c1", entry[0]), entry[0]))
            if not group:
                raise ValueError(f"Missing validation stratum: {country}, singleton={singleton}")
            chosen.append(group[0])

    remaining = [entry for entry in eligible if entry not in chosen]
    remaining.sort(key=lambda entry: (not entry[2], stable_hash(seed, "stage_c1", entry[0]), entry[0]))
    chosen.extend(remaining[:count - len(chosen)])
    if len(chosen) != count:
        raise ValueError("Insufficient validation queries")
    return [entry[0] for entry in chosen]


def collect_relevant_postings(paths, queries, truth_owners, max_posting, max_candidates, max_rescued, guard, run_log, work_deadline):
    consumers = defaultdict(set)
    query_cheap_keys = {}
    query_simhash_keys = {}
    for query_id, query in queries.items():
        keys = cheap_blocking_keys(query["business_name"], query["business_address"])
        query_cheap_keys[query_id] = keys
        query_simhash_keys[query_id] = {key for key in blocking_keys(query["business_name"], query["business_address"]) if key.startswith("sh")}
        for key in keys:
            consumers[(query["country"], key)].add(query_id)
    required_by_country = defaultdict(set)
    for country, key in consumers:
        required_by_country[country].add(key)

    counts = defaultdict(int)
    postings = defaultdict(list)
    rescued = defaultdict(set)
    truth_target_keys = {}
    truth_target_simhash = {}
    country_counts = defaultdict(int)
    for source in ("s2", "s3"):
        run_log.event(f"{source}_pass", "started", guard)
        row_count = 0
        started = time.perf_counter()
        for row in guarded(rows(paths[source], SOURCE_HEADER), guard, work_deadline):
            row_count += 1
            country_counts[row["country"]] += 1
            required = required_by_country.get(row["country"])
            if not required:
                continue
            row_keys = cheap_blocking_keys(row["business_name"], row["business_address"])
            matched_keys = row_keys & required
            for query_id, families in family_rescue_queries(row["country"], matched_keys, consumers).items():
                rescued[query_id].add(row["entity_id"])
                if len(rescued[query_id]) > max_rescued:
                    run_log.event("candidate_cap", "failed", guard, source=source, rows_seen=row_count, query_id=query_id, candidate_kind="cross_family_rescue", evidence_families=sorted(families), count=len(rescued[query_id]), limit=max_rescued)
                    raise RuntimeError(f"Rescue candidate limit exceeded: query={query_id}, count={len(rescued[query_id])}, limit={max_rescued}")
            for key in matched_keys:
                lookup = (row["country"], key)
                counts[lookup] += 1
                if counts[lookup] <= max_posting:
                    postings[lookup].append(row)
                elif counts[lookup] == max_posting + 1:
                    postings[lookup].clear()
            owner = truth_owners.get(row["entity_id"])
            if owner is not None:
                truth_target_keys[row["entity_id"]] = row_keys
                truth_target_simhash[row["entity_id"]] = {key for key in blocking_keys(row["business_name"], row["business_address"]) if key.startswith("sh")}
        run_log.event(f"{source}_pass", "completed", guard, rows_seen=row_count, pass_seconds=round(time.perf_counter() - started, 6))

    candidates, skipped = assemble_candidates(queries, consumers, counts, postings, rescued, max_posting)
    try:
        enforce_candidate_caps(candidates, rescued, max_candidates, max_rescued)
    except RuntimeError as error:
        run_log.event("candidate_cap", "failed", guard, candidate_kind="assembled_total", error=str(error))
        raise
    diagnostics = []
    missing_truth_records = set(truth_owners) - set(truth_target_keys)
    if missing_truth_records:
        raise RuntimeError(f"Missing {len(missing_truth_records)} truth target records")
    for target_id, query_id in sorted(truth_owners.items()):
        cheap_overlap = query_cheap_keys[query_id] & truth_target_keys[target_id]
        per_key_counts = {key: counts[(queries[query_id]["country"], key)] for key in cheap_overlap}
        simhash_overlap = len(query_simhash_keys[query_id] & truth_target_simhash[target_id])
        diagnostic = classify_truth_link(cheap_overlap, per_key_counts, max_posting, simhash_overlap, target_id in candidates[query_id])
        diagnostic.update({"source1_entity_id": query_id, "target_entity_id": target_id})
        diagnostics.append(diagnostic)
    return candidates, country_counts, skipped, len(consumers), diagnostics, {query_id: len(values) for query_id, values in rescued.items()}


def _run(config_path, memory_gib, runtime_minutes, threads, artifact, experiment, run_log):
    if threads != 1:
        raise ValueError("Stage 3C1d permits exactly one worker")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if config["stage"] != "c1d" or config["threads"] != 1:
        raise ValueError("Not the approved Stage 3C1d configuration")
    if memory_gib > 1 or runtime_minutes > 15:
        raise ValueError("Requested limits exceed Stage 3C1d approval")

    root = Path(__file__).resolve().parents[4]
    train = root / "dataset" / "train"
    paths = {"s1": train / "train_source1.tsv", "s2": train / "train_source2.tsv", "s3": train / "train_source3.tsv", "gt": train / "train_ground_truth.tsv"}
    guard = Guard(int(memory_gib * 1024**3), runtime_minutes * 60)
    work_deadline = run_log.start + config["work_deadline_seconds"]
    seed = config["seed"]

    manifest = {"status": "running", "config": config, "python": sys.version, "platform": platform.platform(), "thread_environment": {key: os.environ.get(key) for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")}, "inputs": {key: {"bytes": path.stat().st_size, "mtime_ns": path.stat().st_mtime_ns} for key, path in paths.items()}}
    write_json(experiment / "manifest.json", manifest)

    stage_a = root / "artifacts" / "pilot" / "stage_a"
    run_log.event("cohort_inputs", "started", guard)
    with (stage_a / "selected_s1.tsv").open(encoding="utf-8", newline="") as handle:
        metadata = {row["source1_entity_id"]: {"country": row["country"], "singleton": row["singleton"] == "true", "partition": row["partition"]} for row in csv.DictReader(handle, delimiter="\t")}
    with (stage_a / "pilot_candidate_pairs.tsv").open(encoding="utf-8", newline="") as handle:
        stage_a_candidates = {row["source1_entity_id"]: set(filter(None, row["candidate_entity_ids"].split(","))) for row in csv.DictReader(handle, delimiter="\t")}
    run_log.event("cohort_inputs", "completed", guard)

    truth = {entity_id: set() for entity_id in metadata}
    run_log.event("ground_truth_pass", "started", guard)
    gt_rows = 0
    for row in guarded(rows(paths["gt"], GT_HEADER), guard, work_deadline):
        gt_rows += 1
        if row["source1_entity_id"] in truth:
            truth[row["source1_entity_id"]].update(matches(row["matched_entity_ids"]))
    run_log.event("ground_truth_pass", "completed", guard, rows_seen=gt_rows)
    selected_ids = select_queries(metadata, truth, stage_a_candidates, seed, config["query_count"])

    queries = {}
    run_log.event("source1_pass", "started", guard)
    s1_rows = 0
    for row in guarded(rows(paths["s1"], SOURCE_HEADER), guard, work_deadline):
        s1_rows += 1
        if row["entity_id"] in selected_ids:
            queries[row["entity_id"]] = row
    run_log.event("source1_pass", "completed", guard, rows_seen=s1_rows)
    if set(queries) != set(selected_ids):
        raise ValueError("Selected query records are missing")

    truth_owners = {target: query_id for query_id in selected_ids for target in truth[query_id]}
    candidates, country_counts, skipped, relevant_keys, diagnostics, rescue_counts = collect_relevant_postings(paths, queries, truth_owners, config["max_posting"], config["max_candidates_per_query"], config["max_rescue_candidates_per_query"], guard, run_log, work_deadline)
    run_log.event("candidate_assembly", "started", guard)
    counts = [len(candidates[item]) for item in selected_ids]
    if max(counts) > config["max_candidates_per_query"]:
        raise RuntimeError("Per-query candidate stop limit exceeded")

    retrieval = retrieval_metrics(truth, candidates, selected_ids)
    comparisons = sum(country_counts[queries[item]["country"]] for item in selected_ids)
    known_miss_queries = [item for item in selected_ids if truth[item] - stage_a_candidates.get(item, set())]
    run_log.event("candidate_assembly", "completed", guard, candidate_pairs=sum(counts))

    artifact.mkdir(parents=True)
    run_log.event("artifact_write", "started", guard)
    write_entity_lists(artifact / "pilot_candidate_pairs.tsv", "candidate_entity_ids", candidates, selected_ids)
    with (artifact / "selected_queries.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["source1_entity_id", "country", "singleton", "partition", "stage_a_miss"])
        for item in sorted(selected_ids):
            writer.writerow([item, metadata[item]["country"], str(metadata[item]["singleton"]).lower(), metadata[item]["partition"], str(item in known_miss_queries).lower()])
    with (artifact / "truth_link_diagnostics.tsv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["source1_entity_id", "target_entity_id", "retrieved", "classification", "cheap_overlap_count", "rare_cheap_key_count", "capped_cheap_key_count", "simhash_band_overlap_count"]
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader(); writer.writerows(diagnostics)

    resources = guard.report()
    metrics = {
        "status": "running",
        "stage": "3C1d",
        "candidate_strategy": "query-aware cheap keys with cross-family name-plus-address rescue; SimHash diagnostics only",
        "scope": "complete training S2 and S3 pools only when both pass-completion events exist",
        "query_count": len(selected_ids),
        "query_mix": {f"{country}_{kind}": sum(metadata[item]["country"] == country and metadata[item]["singleton"] == singleton for item in selected_ids) for country in ("India", "US") for kind, singleton in (("singleton", True), ("non_singleton", False))},
        "known_stage_a_miss_queries": len(known_miss_queries),
        "rescue_candidate_counts": {query_id: rescue_counts.get(query_id, 0) for query_id in sorted(selected_ids)},
        "truth_link_diagnostics": {"count": len(diagnostics), "retrieved": sum(item["retrieved"] for item in diagnostics), "classification_counts": {name: sum(item["classification"] == name for item in diagnostics) for name in sorted({item["classification"] for item in diagnostics})}},
        "dataset_scan_passes": {"ground_truth": 1, "source1": 1, "source2": 1, "source3": 1, "total": 4},
        "retrieval": retrieval,
        "candidate_counts": count_summary(counts),
        "total_candidate_pairs": sum(counts),
        "full_pool_reduction_ratio": 1 - sum(counts) / comparisons,
        "skipped_query_keys": skipped,
        "relevant_query_keys": relevant_keys,
        "projection_note": "Multiply measured mean candidates per query by an independently measured test S1 count; this 10-query probe is a rough estimate and does not approve full inference.",
        "resources": resources,
        "limits": {"threads": threads, "memory_gib": memory_gib, "runtime_minutes": runtime_minutes, "artifact_mib": config["max_artifact_mib"], "max_candidates_per_query": config["max_candidates_per_query"], "max_rescue_candidates_per_query": config["max_rescue_candidates_per_query"]},
    }
    write_json(experiment / "stage_c1_metrics.json", metrics)
    metrics["disk_bytes"] = disk_bytes(artifact, experiment)
    if metrics["disk_bytes"] > config["max_artifact_mib"] * 1024**2:
        metrics.update({"status": "failed", "stop_condition": "artifact_limit"})
        write_json(experiment / "stage_c1_metrics.json", metrics)
        raise RuntimeError("Artifact limit exceeded")
    if retrieval["link_recall"] < 1 or retrieval["whole_truth_retention"] < 1:
        metrics.update({"status": "failed", "stop_condition": "retrieval_gate"})
        write_json(experiment / "stage_c1_metrics.json", metrics)
        raise RuntimeError("Stage 3C1 retrieval gate failed")
    metrics["status"] = "completed"
    write_json(experiment / "stage_c1_metrics.json", metrics)
    manifest["status"] = "completed"
    write_json(experiment / "manifest.json", manifest)
    run_log.event("artifact_write", "completed", guard, disk_bytes=metrics["disk_bytes"])
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


def run(config_path, memory_gib, runtime_minutes, threads):
    root = Path(__file__).resolve().parents[4]
    artifact = root / "artifacts" / "pilot" / "stage_c1d"
    experiment = root / "experiments" / "runs" / "stage3c1d_full_pool_probe"
    if artifact.exists() or experiment.exists():
        raise FileExistsError("Refusing to overwrite Stage 3C1d artifacts")
    experiment.mkdir(parents=True)
    run_log = RunLog(experiment / "run.jsonl")
    run_log.event("run", "started", threads=threads, memory_gib=memory_gib, runtime_minutes=runtime_minutes)
    try:
        result = _run(config_path, memory_gib, runtime_minutes, threads, artifact, experiment, run_log)
    except BaseException as error:
        run_log.event("run", "finished", exit_status="failed", exit_code=1, error_type=type(error).__name__, error=str(error))
        raise
    run_log.event("run", "finished", exit_status="success", exit_code=0)
    return result
