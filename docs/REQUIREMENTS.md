# Verified Competition Requirements

## Authority and source precedence

The supplied challenge materials are authoritative. This document records the conservative interpretation when they differ.

| Source | Local path | Role |
|---|---|---|
| Problem statement | `amazon_ml_challenge_problem_statement.md` | Task, data, outputs, metric, package, constraints, fair play |
| Challenge guidelines | `guidelines_and_key_instructions_amazon_ml_challenge.md` | Window, submissions/day, artifacts, eligibility, access rules |
| Supplied README | `README.md` | Structured copy of problem statement and reproduction guidance |
| Methodology template | `Documentation_template.md` | Required methodology sections |
| Validator | `utils/validate_submission.py` | Local format and coverage checks |

If these notes ever disagree with newly supplied official material, stop and resolve the conflict before implementation.

## Task

- Source 1 is a deduplicated reference source.
- For every test Source 1 entity, predict zero, one, or multiple matching entity IDs from test Source 2 and Source 3.
- A Source 1 entity may be a singleton.
- Candidate generation and final matching are separate pipeline stages.
- The submitted candidate set must be the exact final set scored by the matching model, not an earlier broad blocking output.

Source: problem statement and `README.md`.

## Input schemas

All supplied data files are tab-separated and must be read with an explicit tab delimiter.

Source files use exactly:

```text
entity_id
business_name
business_address
country
```

Ground truth uses exactly:

```text
source1_entity_id
matched_entity_ids
```

`matched_entity_ids` is a comma-separated list and is empty for a singleton.

Source: problem statement and `README.md`; headers independently verified in Stage 1 against all seven TSVs.

## Country handling

- Training contains India and US.
- Test additionally contains France.
- Treat country as an open set of strings. Do not hard-code or one-hot the pipeline only to India and US.
- Every test entity, including France, must appear in the final output.

Source: problem statement and `README.md`.

## Evaluation

The leaderboard metric is macro F0.5 over Source 1 entities:

```text
F0.5 = 1.25 * precision * recall / (0.25 * precision + recall)
```

Calculate the score separately for each S1 entity and average over all S1 entities. For singleton truth:

- Empty prediction: entity score 1.0.
- Any non-empty prediction: entity score 0.0.

For non-singleton truth, an empty prediction scores 0.0. Threshold selection must use this end-to-end entity metric rather than pairwise accuracy.

Source: problem statement and `README.md`.

## Required outputs

`output/matching_results.tsv`:

```text
source1_entity_id\tmatched_entity_ids
```

`output/candidate_pairs.tsv`:

```text
source1_entity_id\tcandidate_entity_ids
```

Both files must:

- Be UTF-8 tab-separated text with the exact header.
- Contain exactly one row for every test S1 ID.
- Use an empty second field for an empty list.
- Contain only existing test S2/S3 IDs in list fields.
- Contain no duplicate S1 rows and no duplicate IDs within a list.
- Never contain an S1 ID in a target list.

Additionally, every final match must occur in that S1's final candidate set. The project treats this as a hard assertion.

Source: problem statement, `README.md`, and validator.

## Validation requirements

The supplied validator checks headers, row uniqueness, S1 coverage, prefixes, duplicate list members, and optionally target existence. Its default target-existence check is off, and candidate absence or match-not-in-candidates can produce only warnings.

Project policy is stricter:

- `candidate_pairs.tsv` is mandatory.
- Unknown S2/S3 IDs are fatal.
- `matches` must be a subset of `candidates` for every S1.
- Run the supplied validator and independent checks before packaging.

Source: `utils/validate_submission.py` and problem statement.

## Final package

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

The filled methodology must cover methodology, blocking, model architecture/features, experiments, conclusions, and other relevant information. Code must reproduce training and inference.

Source: problem statement, `README.md`, documentation template, and challenge guidelines.

## Fair play and operational rules

- No external business lookup, registry, map, geocoder, entity-resolution service, or outside identity data.
- No external data augmentation.
- Do not use multiple participant identities or simultaneous challenge logins.
- Maximum five portal submissions per day over the three-day challenge.
- Challenge window: 25 September 2026 00:00 IST through 27 September 2026 23:59 IST.
- Preserve submission version history.
- Do not upload or share anything without explicit user instruction.

Source: challenge guidelines and problem statement.

## Model constraint

Any final pretrained model must have an MIT or Apache 2.0 licence and no more than 8 billion parameters. Verify the exact artifact licence before download or use. Classical locally trained models still require package-licence documentation.

Source: problem statement and `README.md`.

## Conservative resolutions of source conflicts

1. Guidelines request a 1–2-page approach document; the problem statement says there is no page limit. Keep the main methodology concise enough for 1–2 pages and put reproduction detail in the code README; add only a compact appendix when necessary.
2. Guidelines emphasize artifacts for leading teams; the problem statement requires every team to prepare the final package. Prepare the complete package.
3. The problem statement describes unknown IDs as rejection-worthy while the validator says they may only lower score and does not check by default. Treat unknown IDs as fatal.
4. The validator permits a missing candidate file and only warns about subset violations. The competition package requires the file. Treat it and the subset invariant as mandatory.

