# Submission Readiness Audit — 2026-09-26

Authoritative sources: `amazon_ml_challenge_problem_statement.md`,
`guidelines_and_key_instructions_amazon_ml_challenge.md`, `README.md`,
`Documentation_template.md`, and `utils/validate_submission.py`.

| Requirement | Evidence | Status | Remaining action |
|---|---|---|---|
| Two UTF-8 TSV outputs with exact headers | Supplied validator passed `output/matching_results.tsv` and `output/candidate_pairs.tsv` | Complete | None |
| Exactly one row per test S1 | Validator and independent audit: 1,732,544 required and present; no duplicate or missing S1 rows | Complete | None |
| S2/S3 test IDs only; no duplicate list members | Validator found no prefix/list duplicates; independent streaming audit found 0 unknown IDs among 84,062 referenced IDs | Complete | None |
| Final matches are a subset of final candidates | Independent audit returned `matches_subset_candidates: true` | Complete | None |
| Empty/singleton rows preserved | 1,655,262 empty rows in each output; exact singleton accuracy is unavailable without test truth | Format complete; accuracy unverified | None for format |
| France/open-set handling | 259,452 France S1 rows expected and present; code tests preserve France/empty rows | Complete | None |
| Macro F0.5 scoring | Formula and singleton semantics implemented/tested in `metrics.py` and `test_metrics.py` | Implementation complete; final score not measured | Obtain only from authorized validation/leaderboard evaluation |
| Candidate-generation description | Filled methodology and code README describe exact country/name/address signature | Complete | None |
| Runnable source and pinned environment | `code/business_entity_resolution/` contains source, executed config, tests, README, and a standard-library-only requirements file | Complete | Use Python 3.12; no packages to install |
| Model licence and size | No learned or pretrained model is used | Not applicable | None unless the approach changes |
| Methodology document | `Documentation_template.md` completed with verified method, results, limits, and reproduction steps | Complete | Team name/member metadata still required |
| Required zip structure | Archive contains `output/`, `code/business_entity_resolution/`, and filled `Documentation_template.md` | Complete | Rename archive with the official team name before upload |
| No external identity data | Pipeline is standard-library and uses supplied challenge files only | Complete based on reviewed code/config | None |
| Submission/version history | Git history and full-run manifest/log exist | Partial | Team must retain portal submission history; no portal upload was performed here |

## Validated baseline

- Strategy: exact normalized `(country, business_name, business_address)` with 64 disk partitions.
- Recorded full run: 569.4 s wall time; 73,990,144-byte peak working set;
  1,107,184,073 temporary-partition bytes; 50,140,264 output bytes.
- Links: 84,062 candidates and matches; maximum five per S1.
- Supplied validator: PASS. Lightweight tests: 23/23 PASS.
- Independent audit: PASS; 1,732,544 rows, zero unknown target IDs, complete France
  coverage, and match/candidate subset integrity.
- Matching accuracy, macro F0.5, public score, and private score: not measured.

| File | Bytes | SHA-256 |
|---|---:|---|
| `output/matching_results.tsv` | 25,070,131 | `D337FE284598EE59F9F512AF9B63FCB48C260BDB9CDF53B1EDCFBCE0C4473500` |
| `output/candidate_pairs.tsv` | 25,070,133 | `4204DEEFB8938F6AC3889E831116EEA63396EB3AB6D4E8C5A8C45617D5B5A285` |

Pre- and post-validation hashes were identical.

## Provenance and exclusions

The completed run is evidenced by `experiments/runs/submission_exact_v1/{manifest.json,metrics.json,run.jsonl}`
and partitions under `artifacts/submission_exact/submission_exact_v1/`. The manifest records
Python 3.12.10, the full mode, the executed strategy/config values, input file metadata, and a
successful final status. The code implementing the run was committed immediately afterward as
`5490ca6`; because the run manifest does not record a Git commit or source hash, exact source-to-run
identity remains unverified.

Stage 3A/3B and C1-series runs, pilot outputs, smoke partitions, caches, and failed/partial logs
are exploratory evidence only. They are excluded from the package and Git, as are datasets,
full-run temporary partitions, credentials, and the archive itself. The two validated TSV files
are included in the package but remain generated local artifacts outside Git.

## Unverified metadata

The official team name and team-member list were not present in the supplied repository. They
remain explicitly marked unverified in the methodology. The locally prepared archive uses a
generic filename and must be renamed to `<team_name>_submission.zip` after those details are
confirmed. No upload or competition submission was performed.
