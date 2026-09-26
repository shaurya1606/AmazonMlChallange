# Experiment Log

The blank fields below define the record required for future runs.

## Fixed project controls

- Default seed: `20260925`
- Primary validation fraction: `0.20`
- Split unit: `source1_entity_id`
- Stratification: `(country, is_singleton)`
- Metric: per-S1 macro F0.5, with explicit singleton handling
- Candidate evaluation: true-link recall and whole-truth-set retention before matching

## Run record schema

Create one section per executed run only after it finishes or fails. Never pre-populate metric fields.

```text
Experiment ID:
Status: completed | failed | interrupted
Start/end time and timezone:
Git commit or source snapshot hash:
Python and dependency versions:
Configuration file and hash:
Random seed:
Input file sizes/hashes:
Split manifest/hash:

Normalization:
Candidate configuration:
Feature configuration:
Model and licence:
Training-negative construction:
Decision rule/threshold:

Validation S1 count:
Validation positive-link count:
Candidate true-link recall:
S1 all-true-links-retained rate:
Candidates per S1 — mean/median/p95/max:
Reduction ratio:
Macro F0.5:
Singleton accuracy:
Non-singleton macro F0.5:
False-positive links:
False-negative links:

Wall-clock runtime:
Peak resident memory:
Disk written:
Output/artifact paths and hashes:
Notes and error analysis:
Decision: reject | retain | selected
```

## Comparison rule

Compare model changes on the same fixed split and candidate-evaluation definitions. If the split, data population, or metric changes, start a separately labeled comparison series rather than placing scores in the same ranking.

Public leaderboard results, if later supplied by the user, must be recorded separately and must not be presented as a reliable private-leaderboard estimate.

## Stage 3B bounded pilot — 2026-09-26

- Status: completed once; rules only, 100 S1 and 10,000 sampled S2/S3 targets, one CPU thread.
- Tests: 14 passed in 0.021 s.
- Reads: two ground-truth scans and one scan each of S1, S2, and S3 (five complete TSV scans total).
- Retrieval: 194/194 true links, 50/50 non-singleton S1 with all truth retained; all 14 Stage 3A misses recovered and no Stage 3A hit lost.
- Candidate load: 35,505 pairs; mean 355.05, median 331, p95 815.15, max 960 per S1; sample-conditioned reduction ratio 0.92899.
- Leakage audit: zero validation-owned targets labeled as training negatives; 83 such candidates ignored.
- Resources: 453.826 s wall, 421.594 s CPU, 128,176,128-byte peak working set, 764,340 bytes written to ignored pilot/run directories.
- Decision: stop after the approved pilot. Recall gates passed, but runtime did not improve over Stage 3A and candidate volume increased; no full-data scaling is approved.

## Exact-signature local submission — 2026-09-26

- Completed a one-thread, disk-partitioned exact `(country, normalized name, normalized address)` test run: 1,732,544 S1 rows, 84,062 candidate/match links, 569.4 s wall time, 73,990,144-byte peak working set, 1,107,184,073 partition bytes, and 50,140,264 output bytes. The supplied validator passed; an independent streaming check confirmed all 259,452 France rows, match/candidate subset integrity, and zero unknown target IDs. This is a precision-first fallback with intentionally limited recall under noisy name/address variants.

## Submission-readiness audit — 2026-09-26

- Revalidated the saved exact-signature outputs without regeneration: supplied validator PASS,
  23/23 lightweight tests PASS, and independent streaming audit PASS for coverage, target IDs,
  France rows, and match/candidate containment. Pre/post SHA-256 hashes were identical. Prepared
  and locally verified the required zip structure; matching accuracy and macro F0.5 remain
  unmeasured.
