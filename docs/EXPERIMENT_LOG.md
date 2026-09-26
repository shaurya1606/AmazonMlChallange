# Experiment Log

This is the concise chronological record. Raw manifests, metrics, and durable JSONL logs remain
unchanged under `experiments/runs/`; pilots and partitions remain under `artifacts/`.

## Fixed controls

- Default seed: `20260925`.
- Primary validation split: 20% at the S1 entity level, stratified by
  `(country, is_singleton)`, with all owned positives kept together.
- Validation-positive targets are excluded from training negatives and hard-negative mining.
- Primary evaluation definitions: candidate link recall, whole-truth-set retention, and per-S1
  macro F0.5 with explicit singleton handling.
- Public leaderboard results, if later supplied, must remain separate from local validation.
- Compare changes only on the same split and metric definitions; otherwise start a separately
  labeled comparison series.

## Chronology

### Stage 1 audit — 2026-09-25 — completed

Streamed all seven supplied TSVs and measured schemas, rows, missingness, countries, duplicates,
ground-truth coverage, ownership, and distractor counts. The retained audit results are in the
[project guide](PROJECT_GUIDE.md).

### Stage 2 scaffold and validation design — 2026-09-25 — completed

Established repository protection, deterministic S1-level splitting, positive-target ownership,
training-negative isolation, metric definitions, experiment logging, and source/config/test
scaffolding. No package installation, training, or prediction generation occurred in this stage.

### Stage 3A bounded rules pilot — 2026-09-26 — completed, not selected

- Scope: 100 S1 and 10,000 sampled targets; one CPU thread; rules only.
- Retrieval: 180/194 links (92.7835%); 42/50 non-singletons retained all truth (84%).
- Candidate pairs: 9,171; mean 91.71, median 50.5, p95 300.8, max 491.
- Recorded pilot scores: calibration macro F0.5 0.97424; holdout macro F0.5 0.92112.
  These are tiny sampled-pilot results, not final-baseline or leaderboard scores.
- Resources: 431.837 s wall, 393.422 s CPU, 89,251,840-byte peak working set, 424,499 bytes written.
- Decision: reject as final candidate retrieval because 14 truth links were missed.

### Stage 3B bounded rules pilot — 2026-09-26 — completed, not scaled

- Same 100-S1/10,000-target cohort; one CPU thread; five complete TSV scans.
- Tests: 14/14 passed in 0.021 s. Scans: ground truth twice and S1/S2/S3 once each.
- Retrieval: 194/194 links and 50/50 whole-truth retention; all 14 Stage 3A misses recovered.
- Candidate pairs: 35,505; mean 355.05, median 331, p95 815.15, max 960.
- Leakage audit: zero validation-owned targets labeled as negatives; 83 such candidates ignored.
- Recorded pilot scores: calibration macro F0.5 0.97424; holdout macro F0.5 0.93674.
  These are sample-conditioned and do not establish full-pool performance.
- Resources: 453.826 s wall, 421.594 s CPU, 128,176,128-byte peak working set, 764,340 bytes written.
- Decision: do not scale; retrieval improved but runtime did not and candidate volume increased.

### Stage 3C1 full-pool probe — 2026-09-26 — failed

The S2 pass exceeded the intended deadline and failed at 968.116 s. S3 was not started; no
metrics or pilot artifacts were produced. The manifest remained `running`, but the durable run
log records final exit code 1, so the run is failed rather than complete.

### Stage 3C1b query-aware probe — 2026-09-26 — completed scans, failed retrieval gate

- Ten-query cohort; one complete S2 pass and one complete S3 pass.
- Retrieval: 11/14 links (78.5714%); 1/4 non-singletons retained all truth.
- Candidate pairs: 2,693; mean 269.3, median 131.5, p95 705.25, max 784; one zero-candidate query.
- Resources: 715.303 s wall, 28,647,424-byte peak working set, 42,315 bytes written.
- Decision: failed the retrieval gate. The ten-query result does not generalize to all records.

### Stage 3C1c rescue probe — 2026-09-26 — failed, partial

Stopped at 61.372 s during an incomplete S2 pass when a query exceeded the 100,000-candidate
limit. S3 was not started and no full-pool recall metric was produced.

### Stage 3C1d evidence-family rescue probe — 2026-09-26 — failed, partial

Stopped at 46.065 s during S2 row 185,481. Query `S1-276200793` accumulated 10,001
cross-family rescue candidates against a 10,000 limit. S2 and S3 were incomplete; no recall
claim is valid for this run.

### Exact-signature smoke run — 2026-09-26 — completed

- Scope: first 100,000 rows per test source; 64 disk partitions.
- Output: 100,000 S1 rows, 120 candidate/match links, 99,880 empty rows, 14,983 France rows.
- Resources: 21.467 s wall, 24,535,040-byte peak working set, 28,547,022 partition bytes,
  2,780,330 output bytes.
- Decision: resource behavior supported proceeding to the exact-signature full run; this smoke
  run did not measure matching accuracy.

### Exact-signature full baseline — 2026-09-26 — completed and selected

- Method: exact `(country, normalized name, normalized address)` using 64 disk partitions.
- Output: 1,732,544 S1 rows, 84,062 candidate/match links, 1,655,262 empty rows, 77,282
  non-empty rows, 259,452 France rows; maximum five candidates per S1.
- Usable target signatures: 4,757,865 S2 and 4,946,218 S3. Missing-address targets skipped:
  129,408 S2 and 136,098 S3.
- Resources: 569.417 s wall, 530.609 s CPU, 73,990,144-byte peak working set,
  1,107,184,073 partition bytes, and 50,140,264 output bytes.
- Decision: selected as the reproducible precision-first fallback. No final validation F0.5 or
  leaderboard score was measured.

### Submission-readiness audit — 2026-09-26 — completed

The supplied validator passed, 23/23 lightweight tests passed, and the independent verifier
confirmed complete S1/France coverage, zero unknown target IDs, and match/candidate containment.
Pre/post output hashes were identical. See the [submission guide](SUBMISSION_GUIDE.md).

## Provenance limits

The full run is supported by:

- `experiments/runs/submission_exact_v1/manifest.json`
- `experiments/runs/submission_exact_v1/metrics.json`
- `experiments/runs/submission_exact_v1/run.jsonl`
- `artifacts/submission_exact/submission_exact_v1/partitions/`

The manifest records Python 3.12.10, input sizes/mtimes, full mode, configuration, platform, and
completion. The implementation was committed immediately afterward as `5490ca6`, but the run
manifest did not record a Git commit or source hash. Exact source-to-run identity is therefore
**unverified**. Failed C1-series manifests may still say `running`; their durable run logs and
the statuses above are the authoritative project interpretation.
