# Experiment Log

No experiments have been run yet. This file defines the record required for each future run; blank fields below are a schema, not measured results.

## Fixed project controls

- Default seed: `20260925`
- Primary validation fraction: `0.20`
- Split unit: `source1_entity_id`
- Stratification: `(country, is_singleton)`
- Metric: per-S1 macro F0.5, with explicit singleton handling
- Candidate evaluation: true-link recall and whole-truth-set retention before matching

## Run record schema

Create one section per executed run only after it finishes or fails. Never pre-populate metric fields.

```text
Experiment ID:
Status: completed | failed | interrupted
Start/end time and timezone:
Git commit or source snapshot hash:
Python and dependency versions:
Configuration file and hash:
Random seed:
Input file sizes/hashes:
Split manifest/hash:

Normalization:
Candidate configuration:
Feature configuration:
Model and licence:
Training-negative construction:
Decision rule/threshold:

Validation S1 count:
Validation positive-link count:
Candidate true-link recall:
S1 all-true-links-retained rate:
Candidates per S1 — mean/median/p95/max:
Reduction ratio:
Macro F0.5:
Singleton accuracy:
Non-singleton macro F0.5:
False-positive links:
False-negative links:

Wall-clock runtime:
Peak resident memory:
Disk written:
Output/artifact paths and hashes:
Notes and error analysis:
Decision: reject | retain | selected
```

## Comparison rule

Compare model changes on the same fixed split and candidate-evaluation definitions. If the split, data population, or metric changes, start a separately labeled comparison series rather than placing scores in the same ranking.

Public leaderboard results, if later supplied by the user, must be recorded separately and must not be presented as a reliable private-leaderboard estimate.

