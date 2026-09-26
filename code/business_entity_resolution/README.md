# Business Entity Resolution Pipeline

This directory is the self-contained code location required by the final competition package.

Current status: a standard-library, rules-only exact-signature baseline has produced validator-clean local submission files. It is a precision-first fallback rather than a high-recall final model.

## Runtime target

- Python 3.12
- Default seed: `20260925`
- Input data remains outside this directory under the workspace `dataset/` tree.

## Planned source responsibilities

Future Stage 3 implementation will place modules under `src/business_entity_resolution/` for:

- Input/schema validation and chunked TSV reading
- Deterministic split construction
- Text normalization
- Candidate generation
- Pair feature construction
- Matching model training/scoring
- Per-entity evaluation
- Output writing and independent validation

Exact commands will be documented only after they exist and have been executed successfully.

## Reproduce the exact-signature submission

From this directory with Python 3.12:

```powershell
$env:PYTHONPATH='src'
python -m business_entity_resolution.cli submission --config configs/submission_exact.json --mode full
python ..\..\utils\validate_submission.py --matching ..\..\output\matching_results.tsv --candidate ..\..\output\candidate_pairs.tsv --test-dir ..\..\dataset\test
python -m business_entity_resolution.verify
```

The pipeline uses 64 on-disk hash partitions and exact normalized country, name, and address equality. It writes one row for every test S1, including France and empty-match cases. Generated partitions and outputs are outside this code directory and are excluded from Git.

## Reproducibility contract

- Never mutate supplied inputs.
- Record configuration, seed, input identity, runtime, peak memory, metrics, and artifact hashes for each run.
- Fit all learned transformations on the training partition only.
- Validation-positive targets must never enter training negatives or candidate mining.
- Candidate outputs must be the exact pairs scored by the final matcher.
