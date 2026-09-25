# Project Instructions

These instructions apply to the entire `student_resource` workspace.

## Competition integrity

- Use only the supplied challenge data for business identity information.
- Never query websites, registries, maps, geocoders, search engines, APIs, or external datasets to resolve an entity.
- Never send business records to an external service.
- Do not use test ground truth. None is supplied.
- A pretrained model may be considered only after its exact licence and parameter count are verified. The competition permits MIT or Apache 2.0 models up to 8 billion parameters.
- Do not register or attempt the challenge through multiple identities.

## Input protection

- Treat `dataset/train/`, `dataset/test/`, the supplied PDFs/Markdown, `README.md`, `Documentation_template.md`, and `utils/validate_submission.py` as immutable inputs.
- Read TSVs with an explicit tab delimiter and UTF-8-compatible encoding.
- Put transformations, indexes, models, caches, and outputs in separate generated locations.
- Never commit datasets, generated indexes, model weights, credentials, temporary files, outputs, or submission archives.

## Stage approvals

- Work stage by stage. Before each major stage, report what is known, the exact planned reads/writes/commands, expected results, and material runtime/storage/uncertainty.
- Wait for explicit approval before starting a new major stage.
- Ordinary commands within an approved stage do not require repeated confirmation.
- Do not claim a score, validation result, completed run, or validator pass unless it was actually measured.

## Actions requiring explicit approval

- Installing or upgrading packages.
- Any network access, download, model-weight retrieval, or external data access.
- Training a model or running full-scale candidate generation.
- Generating final test predictions or overwriting versioned outputs.
- Spending cloud/AWS credits, deploying services, publishing code/data, sharing files externally, or uploading to the competition portal.
- Deleting supplied data or material generated artifacts.

## Validation and outputs

- Use seed `20260925` unless an experiment explicitly records another approved seed.
- Split at the S1 entity level. Keep all positives owned by an S1 in that S1's partition.
- Never use validation-positive S2/S3 targets as training negatives, training candidates, or hard-negative-mining inputs.
- Evaluate candidate recall separately from final per-S1 macro F0.5.
- Treat `candidate_pairs.tsv` as required and enforce final matches as a strict subset of final candidates.
- Treat unknown output IDs as a fatal internal error even though the supplied validator's default mode does not check them.
- Every test S1, including France, must receive exactly one output row.

