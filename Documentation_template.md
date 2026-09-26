# ML Challenge 2026: Business Entity Resolution Solution Template

**Team Name:** Unverified — not provided

**Team Members:** Unverified — not provided

**Submission Date:** 26 September 2026

---

## 1. Executive Summary
This submission is a conservative, standard-library baseline that links a Source 1 record only
to Source 2/3 records with the same country and the same normalized full business name and
address. It favors precision and bounded laptop resource use; it does not use external data,
a learned model, or a pretrained model.

---

## 2. Methodology

### 2.1 Problem Analysis
The supplied materials identify spelling, punctuation, abbreviation, ordering, transliteration,
and missing-address noise. The completed run also recorded 129,408 Source 2 and 136,098 Source
3 rows without a usable full signature. France is absent from training but present in test, so
country is handled as an unrestricted string rather than a fixed India/US enumeration.

### 2.2 Solution Strategy
Records are streamed as UTF-8 TSV, normalized with deterministic Unicode/text rules, assigned
to one of 64 on-disk hash partitions, and joined within each partition on the compound key
`(country, normalized business_name, normalized business_address)`. The same exact links form
the final candidate set and final match set. Output writing preserves every Source 1 row,
including France and empty-match rows.

**Approach Type:** Exact-rule blocking and matching (no classifier)

**Core Innovation:** A deterministic, disk-partitioned implementation that keeps the full test
run within laptop memory while enforcing country gating and complete Source 1 coverage.

---

## 3. Candidate Generation (Blocking)
The final candidate set contains only exact compound-signature collisions.

- **Blocking keys used:** country, normalized full business name, normalized full address.
- **Candidate pairs generated:** 84,062 across 1,732,544 test Source 1 records.
- **How true-match loss was assessed:** full-test recall cannot be measured because no test
  ground truth is supplied. The exact rule is known to miss noisy variants and targets without
  a usable address; no claim of complete recall is made.

---

## 4. Matching Model

**Features used:**
- Name features: normalized full-string equality
- Address features: normalized full-string equality; a non-empty address is required
- Other: exact country equality

**Model type:** deterministic rule; no learned or pretrained model

**Threshold selection method:** not applicable. Consequently, the competition's pretrained-model
license and parameter-count constraint is not invoked by this baseline.

---

## 5. Results & Error Analysis

- **F_0.5 Score (macro):** not measured for this final exact-signature baseline; no leaderboard
  score is claimed.
- **Common false positives (wrong merges):** not measured. A possible limitation is distinct
  businesses sharing identical normalized names and addresses.
- **Common false negatives (missed matches):** expected for spelling, abbreviation,
  transliteration, word-order, or address differences and for missing addresses; final-test
  error counts are unavailable without labels.

Format validation passed on 26 September 2026. Both files contain 1,732,544 rows; 1,655,262
rows have empty lists and 77,282 have non-empty lists. An independent streaming audit found
zero unknown target IDs, all 259,452 France Source 1 rows, and no match outside its candidate
set. These are structural checks, not accuracy measurements.

---

## 6. Conclusion
The baseline produces complete, validator-clean outputs using one CPU process and bounded
memory. Its measured full run took 569.4 seconds, peaked at 73,990,144 bytes of working set,
used 1,107,184,073 bytes for temporary partitions, and wrote 50,140,264 bytes of outputs.
The result is suitable as a reproducible precision-first fallback, but its matching accuracy
and macro F0.5 remain unverified.

---

## Appendix

### A. Code Artefacts
The package contains `code/business_entity_resolution/`: implementation modules under `src/`,
the executed configuration under `configs/submission_exact.json`, lightweight tests under
`tests/`, a reproduction `README.md`, and `requirements.txt`. From that directory, set
`PYTHONPATH=src` and run:

```powershell
python -m business_entity_resolution.cli submission --config configs/submission_exact.json --mode full
python ..\..\utils\validate_submission.py --matching ..\..\output\matching_results.tsv --candidate ..\..\output\candidate_pairs.tsv --test-dir ..\..\dataset\test
python -m business_entity_resolution.verify
```

The first command regenerates outputs and should be run only in a fresh workspace or after
preserving the submitted files. Python 3.12.10 was used; no third-party packages are required.

### B. Additional Results
The recorded full run processed 1,732,544 Source 1 rows, 4,757,865 usable Source 2 signatures,
and 4,946,218 usable Source 3 signatures. Maximum candidates for any Source 1 record was five.
The SHA-256 values are
`D337FE284598EE59F9F512AF9B63FCB48C260BDB9CDF53B1EDCFBCE0C4473500` for
`matching_results.tsv` and
`4204DEEFB8938F6AC3889E831116EEA63396EB3AB6D4E8C5A8C45617D5B5A285` for
`candidate_pairs.tsv`.

---

**Note:** Teams can modify sections according to their approach while maintaining clarity and technical depth.
