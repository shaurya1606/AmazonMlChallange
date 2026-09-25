# Stage 1 Data Audit

## Method and traceability

Audit date: 25 September 2026.

Every TSV was streamed from its local source using Python's `csv.reader` with `delimiter="\t"`, `encoding="utf-8-sig"`, and CSV-aware row parsing. Full business records were not retained in memory. Identifier sets and aggregate counters were retained only long enough to perform exact duplicate, coverage, ownership, and target-existence checks.

Counts below are tied directly to the named source file. A data change requires rerunning the audit rather than editing counts by hand.

## Files, schemas, and missingness

Expected source schema: `entity_id`, `business_name`, `business_address`, `country`.

Expected ground-truth schema: `source1_entity_id`, `matched_entity_ids`.

| Source file | Bytes | Data rows | Missing entity ID | Missing name | Missing address | Missing country |
|---|---:|---:|---:|---:|---:|---:|
| `dataset/train/train_source1.tsv` | 210,069,713 | 2,206,821 | 0 | 0 | 0 | 0 |
| `dataset/train/train_source2.tsv` | 489,301,488 | 5,034,616 | 0 | 0 | 168,967 (3.3561%) | 0 |
| `dataset/train/train_source3.tsv` | 503,705,637 | 5,285,603 | 0 | 0 | 175,916 (3.3282%) | 0 |
| `dataset/test/test_source1.tsv` | 175,022,086 | 1,732,544 | 0 | 0 | 0 | 0 |
| `dataset/test/test_source2.tsv` | 509,456,422 | 4,887,273 | 0 | 0 | 129,408 (2.6479%) | 0 |
| `dataset/test/test_source3.tsv` | 506,002,772 | 5,082,316 | 0 | 0 | 136,098 (2.6779%) | 0 |
| `dataset/train/train_ground_truth.tsv` | 127,015,583 | 2,206,821 | 0 | not applicable | 123,247 empty match lists (5.5848%) | not applicable |

All seven headers exactly matched their expected schemas. Total source records: 24,229,173. Total audited rows including ground truth: 26,435,994. TSV bytes: 2,520,573,701 (approximately 2.35 GiB).

## Structural integrity

Across the six source files:

- Malformed rows: 0
- Blank physical rows: 0
- Duplicate entity IDs within a file: 0
- IDs with an incorrect source prefix: 0

Ground truth:

- Duplicate S1 rows: 0
- Train S1 records missing from ground truth: 0
- Extra ground-truth S1 IDs: 0
- Duplicate IDs inside a match list: 0
- Invalid target prefixes: 0
- Target IDs absent from train S2/S3: 0
- Targets assigned to more than one S1: 0
- Cross-country labeled links: 0

## Country counts

| Source file | India | US | France |
|---|---:|---:|---:|
| `dataset/train/train_source1.tsv` | 883,188 | 1,323,633 | 0 |
| `dataset/train/train_source2.tsv` | 2,017,799 | 3,016,817 | 0 |
| `dataset/train/train_source3.tsv` | 2,115,547 | 3,170,056 | 0 |
| `dataset/test/test_source1.tsv` | 809,986 | 663,106 | 259,452 |
| `dataset/test/test_source2.tsv` | 2,312,565 | 1,871,330 | 703,378 |
| `dataset/test/test_source3.tsv` | 2,405,000 | 1,945,701 | 731,615 |

France accounts for 259,452 test S1 records and is absent from labeled training. Country must remain an open-set string feature/block rather than a closed trained category.

## Ground-truth match distribution

Singletons: 123,247 of 2,206,821 S1 entities (5.5848%).

| Matches per S1 | S1 entities |
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

Total labeled links: 7,638,365. Mean matches per S1: approximately 3.46.

Target coverage:

| Source | Total records | Labeled as a match | Not linked to any S1 |
|---|---:|---:|---:|
| Train S2 | 5,034,616 | 3,693,619 | 1,340,997 |
| Train S3 | 5,285,603 | 3,944,746 | 1,340,857 |

The 2,681,854 unlinked target records are natural distractors. They must be partitioned before training/validation candidate generation so validation remains entity-disjoint.

## Environment at audit time

- `python`: 3.12.10
- `python3`: 3.14.7
- Python 3.12 package inventory: `pip==25.0.1` only
- Physical RAM: approximately 14.9 GiB total; approximately 8.7 GiB free during audit
- Free disk: approximately 90.3 GiB on `D:` and 69.9 GiB on `C:`

Project recommendation: use Python 3.12 and bounded/on-disk processing. A single in-memory representation for all roughly 10 million test targets is high risk on this machine.

## Modeling and validation consequences

- Full Cartesian comparison is infeasible; test scale is roughly 17 trillion possible S1-target pairs.
- Missing-address handling is required for S2/S3; candidate generation must retain a name-only path.
- Country equality is supported by all training labels, but the implementation must work for arbitrary labels such as France.
- Split by S1, never by candidate pair.
- Keep every positive target with its owning S1 partition.
- Do not expose validation-owned positives to training negative generation or hard-negative mining.
- Measure blocking independently from classification and record both link-level recall and whole-truth-set retention.
- Optimize final selection against per-entity macro F0.5, including singleton behavior.

