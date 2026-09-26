# Project Guide

## Purpose and authority

The challenge asks for every test Source 1 entity to be linked to zero or more matching Source 2
or Source 3 records. Source 1 is deduplicated; business identity fields are noisy and no common
identifier exists across sources.

The authoritative local materials are:

| Source | Path | Authority |
|---|---|---|
| Challenge README | [`README.md`](../README.md) | Structured task, output, metric, and package requirements |
| Problem statement | [`amazon_ml_challenge_problem_statement.md`](../amazon_ml_challenge_problem_statement.md) | Task, data, output, evaluation, package, and fair-play rules |
| Guidelines | [`guidelines_and_key_instructions_amazon_ml_challenge.md`](../guidelines_and_key_instructions_amazon_ml_challenge.md) | Challenge window, submission limits, requested artifacts, and access rules |
| Methodology template | [`Documentation_template.md`](../Documentation_template.md) | Required methodology deliverable |
| Supplied validator | [`utils/validate_submission.py`](../utils/validate_submission.py) | Local output-format and coverage checks |

If this guide conflicts with supplied material, the supplied material wins and the discrepancy
must be resolved before further work.

## Requirements checklist

| Requirement | Current status | Primary evidence |
|---|---|---|
| Use only supplied challenge data; no external identity lookup | Complete for reviewed baseline | Standard-library source and recorded configuration |
| Read/write UTF-8-compatible tab-separated files with explicit tabs | Complete | I/O implementation, tests, and validator PASS |
| Predict zero or more test S2/S3 IDs for every test S1 | Complete structurally | [Submission guide](SUBMISSION_GUIDE.md) |
| Preserve empty/singleton rows and prohibit duplicate rows/list members | Complete structurally | [Submission guide](SUBMISSION_GUIDE.md) |
| Treat country as open-set and include France | Complete structurally | 259,452/259,452 France S1 rows present |
| Keep final matches within the final candidate set | Complete | Independent audit PASS |
| Evaluate with per-S1 macro F0.5, including singleton semantics | Implemented and tested; final score not measured | `metrics.py`, `scoring.py`, lightweight tests |
| Supply both output TSVs, runnable code, requirements, and methodology | Complete locally | Verified final archive; see [submission guide](SUBMISSION_GUIDE.md) |
| Pretrained model must be MIT/Apache 2.0 and at most 8B parameters | Not applicable | Baseline uses no learned or pretrained model |
| Preserve version history and obey portal submission limits | Partial | Git history exists; portal history and upload are outside this repository |

Operational requirements from the supplied guidelines:

- Challenge window: 25 September 2026 00:00 IST through 27 September 2026 23:59 IST.
- Maximum five portal submissions per day across the three challenge days.
- Use a desktop or laptop; simultaneous logins are prohibited.
- Do not register or attempt the challenge through multiple identities.
- Preserve submission version history.
- The requested methodology covers the approach, models (none for this baseline), experiments,
  conclusion, blocking strategy, architecture/features, and other relevant information. The
  guidelines request 1–2 pages while the problem statement states no page limit; the completed
  template remains concise.

The leaderboard metric is precision-heavy macro F0.5:

```text
F0.5 = 1.25 * precision * recall / (0.25 * precision + recall)
```

It is calculated separately for every S1 and then averaged. A true singleton scores 1.0 for an
empty prediction and 0.0 for a non-empty prediction. No validation or leaderboard F0.5 has been
measured for the final exact-signature baseline.

## Audited data overview

The Stage 1 audit streamed all TSVs on 25 September 2026 using Python `csv.reader`, an explicit
tab delimiter, and UTF-8-compatible decoding. Counts are tied to the listed source files.

| File | Bytes | Rows | Missing address |
|---|---:|---:|---:|
| `dataset/train/train_source1.tsv` | 210,069,713 | 2,206,821 | 0 |
| `dataset/train/train_source2.tsv` | 489,301,488 | 5,034,616 | 168,967 |
| `dataset/train/train_source3.tsv` | 503,705,637 | 5,285,603 | 175,916 |
| `dataset/train/train_ground_truth.tsv` | 127,015,583 | 2,206,821 | Not applicable; 123,247 empty match lists |
| `dataset/test/test_source1.tsv` | 175,022,086 | 1,732,544 | 0 |
| `dataset/test/test_source2.tsv` | 509,456,422 | 4,887,273 | 129,408 |
| `dataset/test/test_source3.tsv` | 506,002,772 | 5,082,316 | 136,098 |

All seven headers matched the expected schemas. Across the six source files, the audit found no
malformed rows, blank physical rows, duplicate IDs, missing IDs/names/countries, or incorrect ID
prefixes. Ground truth had complete S1 coverage, no duplicate rows or list members, no invalid or
unknown targets, no targets owned by multiple S1 entities, and no cross-country labeled links.
The audit covered 24,229,173 source records and 26,435,994 rows including ground truth, totaling
2,520,573,701 TSV bytes (approximately 2.35 GiB).

### Country counts

| File | India | US | France |
|---|---:|---:|---:|
| Train S1 | 883,188 | 1,323,633 | 0 |
| Train S2 | 2,017,799 | 3,016,817 | 0 |
| Train S3 | 2,115,547 | 3,170,056 | 0 |
| Test S1 | 809,986 | 663,106 | 259,452 |
| Test S2 | 2,312,565 | 1,871,330 | 703,378 |
| Test S3 | 2,405,000 | 1,945,701 | 731,615 |

France is absent from labeled training. France row coverage is validated, but France matching
accuracy is not measured because test ground truth is not supplied.

### Training truth

- Total labeled links: 7,638,365.
- True singletons: 123,247 of 2,206,821 S1 records (5.5848%).
- Mean links per S1: approximately 3.46; observed range: 0–11.
- Train S2 linked/unlinked: 3,693,619 / 1,340,997.
- Train S3 linked/unlinked: 3,944,746 / 1,340,857.
- The 2,681,854 unlinked targets are natural distractors.

| Matches per S1 | S1 records |
|---:|---:|
| 0 | 123,247 |
| 1 | 119,157 |
| 2 | 375,212 |
| 3 | 530,841 |
| 4 | 484,115 |
| 5 | 321,957 |
| 6 | 164,868 |
| 7 | 63,968 |
| 8 | 18,680 |
| 9 | 4,205 |
| 10 | 534 |
| 11 | 37 |

The audit environment used Python 3.12.10. Approximately 14.9 GiB physical RAM was available;
bounded streaming and on-disk processing were therefore selected over a full in-memory target
index.

## Validation and leakage contract

- Default seed: `20260925`.
- Primary validation fraction: 20% at the S1 entity level.
- Keep every positive target with its owning S1 partition.
- Validation-positive S2/S3 targets must not enter training negatives, training candidates,
  hard-negative mining, or threshold selection.
- Candidate retrieval is evaluated separately from final per-S1 macro F0.5.
- Unknown output targets and match/candidate subset violations are fatal project errors even when
  the supplied validator only warns or skips the check by default.

## Current baseline and pipeline flow

The submitted baseline is a deterministic rule, not a learned model:

```text
test S1/S2/S3 TSVs
        ↓ stream and validate
Unicode/text normalization
        ↓ require non-empty normalized name and address for targets
compound signature: (country, normalized name, normalized address)
        ↓ hash into 64 disk partitions
partition-local exact join
        ↓
candidate_pairs.tsv = exact-signature collisions
        ↓ same deterministic decision
matching_results.tsv
        ↓
supplied validator + independent streaming verifier
```

Country is compared as an unrestricted string, so France is retained. Candidate and final match
sets are identical for this baseline. This is a conservative precision-first fallback and is
expected to miss noisy variants and target records without a usable address.

## Source architecture

| Module | Responsibility |
|---|---|
| `io.py` | TSV schema checks and streaming reads |
| `normalize.py` | Deterministic text normalization |
| `split.py`, `validation.py` | Reproducible S1 ownership split and leakage controls |
| `blocking.py`, `bloom.py`, `stage_c.py` | Pilot and diagnostic retrieval components |
| `metrics.py`, `scoring.py` | Candidate and per-S1 evaluation helpers |
| `submission.py` | Disk-partitioned exact-signature full-test pipeline |
| `outputs.py` | Output construction and invariants |
| `resource_limits.py` | Runtime and memory guards |
| `verify.py` | Independent coverage, ID, France, and subset checks |
| `cli.py` | Command-line entry point |

## Repository map

```text
student_resource/
├── README.md, problem statement, guidelines, Documentation_template.md
├── code/business_entity_resolution/   source, configs, tests, code README
├── dataset/                            supplied immutable train/test TSVs; ignored by Git
├── docs/                               project documentation
├── experiments/runs/                   durable run records; ignored by Git
├── artifacts/                          pilots and disk partitions; ignored by Git
├── output/                             validated baseline TSVs; ignored by Git
├── results/                            unchanged local output backups; ignored by Git
├── submission/                         archives/staging/verification; ignored by Git
└── utils/validate_submission.py        supplied validator
```

## Reproducibility and tests

Python 3.12.10 was used; the baseline has no third-party dependencies. From the repository root:

```powershell
$env:PYTHONPATH='code\business_entity_resolution\src'
python -m unittest discover -s code\business_entity_resolution\tests -p 'test_*.py' -v
```

The exact validator and integrity commands are maintained in the
[submission guide](SUBMISSION_GUIDE.md). Full reproduction is documented beside the source in
[`code/business_entity_resolution/README.md`](../code/business_entity_resolution/README.md).
The following command regenerates predictions and must not be used merely to validate saved files:

```powershell
Set-Location code\business_entity_resolution
$env:PYTHONPATH='src'
python -m business_entity_resolution.cli submission --config configs/submission_exact.json --mode full
```

Run evidence and all failed/partial experiments are recorded in the
[experiment log](EXPERIMENT_LOG.md).
