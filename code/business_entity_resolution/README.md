# Business Entity Resolution Pipeline

This directory is the self-contained code location required by the final competition package.

Current status: a standard-library, rules-only exact-signature baseline has produced validator-clean local submission files. It is a precision-first fallback rather than a high-recall final model.

## Runtime target

- Python 3.12
- Default seed: `20260925`
- Input data remains outside this directory under the workspace `dataset/` tree.

## Source responsibilities

Modules under `src/business_entity_resolution/` provide:

- Input/schema validation and chunked TSV reading
- Deterministic split construction
- Text normalization
- Candidate generation
- Exact-signature joining and output construction
- Per-entity evaluation
- Output writing and independent validation

## Reproduce the exact-signature submission

From this directory with Python 3.12:

```powershell
$env:PYTHONPATH='src'
python -m business_entity_resolution.cli submission --config configs/submission_exact.json --mode full
python ..\..\utils\validate_submission.py --matching ..\..\output\matching_results.tsv --candidate ..\..\output\candidate_pairs.tsv --test-dir ..\..\dataset\test
python -m business_entity_resolution.verify
```

The pipeline uses 64 on-disk hash partitions and exact normalized country, name, and address equality. It writes one row for every test S1, including France and empty-match cases. Generated partitions and outputs are outside this code directory and are excluded from Git.

The full recorded run used Python 3.12.10, one process, 569.4 seconds wall time,
73,990,144 bytes peak working set, and 1,107,184,073 bytes of temporary partitions.
No third-party dependencies, learned model, or pretrained model are used. Validation confirms
format and referential integrity only; matching accuracy and leaderboard F0.5 are not measured.

## Reproducibility contract

- Never mutate supplied inputs.
- Record configuration, seed, input identity, runtime, peak memory, metrics, and artifact hashes for each run.
- Fit all learned transformations on the training partition only.
- Validation-positive targets must never enter training negatives or candidate mining.
- Candidate outputs must be the exact pairs scored by the final matcher.
