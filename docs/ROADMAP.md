# Project Roadmap

## Current status

- Stage 1: complete.
- Stage 2: complete when the files in this scaffold have been reviewed.
- Stage 3: awaiting explicit approval.
- No package installation, model training, test inference, or prediction generation has occurred.

## Stage 1 — Resource review and data audit

Completed:

- Reviewed supplied problem, guidelines, README, template, and validator through their local Markdown/source forms.
- Streamed all seven TSVs using an explicit tab delimiter.
- Measured file sizes, row counts, schemas, missingness, country counts, duplicates, malformed rows, singleton rate, and match-count distribution.
- Checked ground-truth coverage, target existence, unique ownership, prefixes, and cross-country labels.
- Inspected RAM, disk, Python versions, and installed packages.

Completion evidence: `docs/DATA_AUDIT.md` and `docs/REQUIREMENTS.md`.

## Stage 2 — Project setup and validation design

Scope:

- Create project governance and source-protection rules.
- Record verified requirements and audit counts.
- Define deterministic leakage-safe validation.
- Define experiment-recording and evaluation contracts.
- Create code/config/test directories without implementing or running a model.

Completion criteria:

- Required documentation files exist and contain measured or explicitly labeled planned information.
- Split unit, strata, deterministic ordering, target ownership, and negative-pool isolation are unambiguous.
- Dataset/output/generated-artifact paths are protected by `.gitignore`.
- No packages are installed and no predictions are created.

## Stage 3 — Reproducible baseline

Awaiting approval. Planned outcomes:

- Conservative Unicode/name/address normalization.
- Scalable, country-aware candidate generation.
- Similarity features and a simple licensed matching model.
- Measured candidate recall, candidates per S1, reduction ratio, runtime, peak memory, singleton performance, and macro F0.5 on the fixed validation split.

Before Stage 3, present exact dependencies, licences, installation/download actions, estimated runtime, storage, and uncertainty for approval.

## Stage 4 — Improvement and model selection

Awaiting completion of Stage 3. Planned outcomes:

- Separate retrieval-miss and classification-error analysis.
- Controlled changes using the same fixed split.
- Realistic hard negatives confined to the training partition.
- Validation-selected threshold emphasizing precision and singleton safety.
- Selected final configuration with evidence, licence record, and resource estimate.

## Stage 5 — Full test inference

Awaiting model selection and explicit approval. Planned outcomes:

- Fit the selected permitted pipeline on training data.
- Process all test S1 records with bounded memory.
- Produce versioned `matching_results.tsv` and `candidate_pairs.tsv`.
- Record configuration, hashes, runtime, peak memory, and output version.

## Stage 6 — Verification and package

Awaiting test outputs and explicit approval. Planned outcomes:

- Run supplied validator with appropriate ID checking.
- Independently verify coverage, uniqueness, prefixes, existence, empty fields, and match/candidate subset.
- Complete code README, pinned requirements, methodology, and exact package structure.
- Create the submission archive locally. Do not upload it without explicit instruction.

## Unresolved decisions

- Baseline dependency set and exact pinned versions.
- Candidate-index implementation appropriate for approximately 10 million targets and available RAM.
- Whether any pretrained representation is justified after the classical baseline; no model weights may be obtained without approval.
- Team name and team-member details for final documentation.

