# Submission Guide

This guide covers the existing validated baseline only. It distinguishes structural validation
from matching accuracy and does not authorize regeneration or portal upload.

## Required outputs

Both files are UTF-8 tab-separated text with exactly one row per test S1:

```text
output/matching_results.tsv
source1_entity_id\tmatched_entity_ids

output/candidate_pairs.tsv
source1_entity_id\tcandidate_entity_ids
```

The second column is a comma-separated list with no duplicate IDs, or an empty field for no
match/candidate. List values must be existing test S2/S3 IDs. S1 IDs are forbidden in lists,
duplicate S1 rows are forbidden, and every final match must occur in the same S1's final
candidate set. `candidate_pairs.tsv` must represent the final candidates actually passed to the
matcher, not an earlier broad blocking stage.

France is an unseen training-country label, but all 259,452 France test S1 records must receive
rows. France coverage is confirmed; France matching accuracy is **not measured** because test
ground truth is unavailable.

## Validation commands

From the repository root, the supplied documented validator invocation is:

```powershell
python utils\validate_submission.py --matching output\matching_results.tsv --candidate output\candidate_pairs.tsv --test-dir dataset\test
```

The default validator checks headers, tabs, row uniqueness/coverage, list duplicates, prefixes,
and match/candidate consistency warnings. Its target-existence option is memory-heavy and off by
default. The project used its bounded independent verifier for the fatal target-ID and subset
checks:

```powershell
$env:PYTHONPATH='code\business_entity_resolution\src'
python -m business_entity_resolution.verify
```

Lightweight tests:

```powershell
$env:PYTHONPATH='code\business_entity_resolution\src'
python -m unittest discover -s code\business_entity_resolution\tests -p 'test_*.py' -v
```

## Confirmed validation evidence

| Check | Measured result |
|---|---|
| Supplied validator | PASS |
| Lightweight tests | 23/23 PASS in 0.464 s during documentation audit |
| Rows in each output | 1,732,544 |
| Empty/non-empty rows | 1,655,262 / 77,282 |
| Duplicate or missing S1 rows | 0 |
| Referenced target IDs | 84,062 |
| Unknown target IDs | 0 |
| Matches outside candidates | 0 |
| France S1 coverage | 259,452 expected and present |

These results establish format, coverage, and referential integrity. They do **not** establish
matching accuracy, candidate recall on test, macro F0.5, or a public/private leaderboard score;
all remain **not measured**.

## Output identity

| File | Bytes | SHA-256 |
|---|---:|---|
| `output/matching_results.tsv` | 25,070,131 | `D337FE284598EE59F9F512AF9B63FCB48C260BDB9CDF53B1EDCFBCE0C4473500` |
| `output/candidate_pairs.tsv` | 25,070,133 | `4204DEEFB8938F6AC3889E831116EEA63396EB3AB6D4E8C5A8C45617D5B5A285` |

The unchanged `results/` backups have the same hashes. Hashes matched before and after the
readiness validation and are checked again after documentation-only work.

## Baseline method and limitations

The baseline exact-joins `(country, normalized full business name, normalized full business
address)` using 64 disk partitions. It uses no classifier, learned parameters, pretrained model,
third-party package, external identity data, or threshold. The competition model-license and
parameter limit is therefore not applicable to this baseline.

Measured full-run resources were 569.417 s wall time, 530.609 s CPU, 73,990,144-byte peak working
set, 1,107,184,073 temporary-partition bytes, and 50,140,264 output bytes. It is intentionally
precision-first and is expected to miss spelling, abbreviation, transliteration, ordering, and
address variants, plus S2/S3 targets without a usable address. False positives, false negatives,
test recall, and final macro F0.5 are not measured.

## Required package

The supplied requirement is:

```text
<team_name>_submission.zip
├── output/
│   ├── matching_results.tsv
│   └── candidate_pairs.tsv
├── code/
│   └── business_entity_resolution/
│       ├── src/
│       ├── README.md
│       └── requirements.txt
└── Documentation_template.md
```

Current verified archive:

```text
submission/amazon_ml_challenge_submission_final.zip
```

- Size: 19,750,057 bytes.
- SHA-256: `B25E195D4D2E9E51B0D5DDB67F668F8F6352CDDE54FB38368FBEF318DA6C1E98`.
- Contents: both validated outputs; completed root methodology; pipeline source, configs, tests,
  README, and requirements file.
- Verification: archive opened successfully, all required paths were present, forbidden-entry
  count was zero, and extracted outputs passed the supplied validator with original hashes.

Excluded from the package and Git: datasets, raw experiment run logs, pilot outputs,
temporary/full-run partitions, caches, credentials, staging/verification folders, and the
archive itself. Raw run evidence remains local under `experiments/runs/` and `artifacts/`.
Earlier archives and all
staging/verification folders remain unchanged but must not be uploaded; use only the final archive.

## Remaining actions and unknowns

- Official team name and team-member list are **unverified** and remain marked as such in
  `Documentation_template.md`.
- Recheck the official naming instruction after the registered team name is known, then rename
  the final archive to `<team_name>_submission.zip`. Do not rename it before that.
- No competition upload has been performed. Portal upload and submission-count tracking remain
  user actions.
- Preserve the final output hashes and rerun the supplied validator after any future packaging
  change.
- Exact source-to-run identity is **unverified** because the completed run manifest contains no
  Git commit or source hash; see the [experiment log](EXPERIMENT_LOG.md).
