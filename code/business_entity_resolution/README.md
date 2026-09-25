# Business Entity Resolution Pipeline

This directory is the self-contained code location required by the final competition package.

Current status: Stage 2 scaffold only. No candidate generator, matching model, training command, or inference command has been implemented or run.

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

## Reproducibility contract

- Never mutate supplied inputs.
- Record configuration, seed, input identity, runtime, peak memory, metrics, and artifact hashes for each run.
- Fit all learned transformations on the training partition only.
- Validation-positive targets must never enter training negatives or candidate mining.
- Candidate outputs must be the exact pairs scored by the final matcher.

