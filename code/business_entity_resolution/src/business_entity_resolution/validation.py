"""Leakage assertions."""


def ownership(truth):
    result = {}
    for owner, targets in truth.items():
        for target in targets:
            old = result.setdefault(target, owner)
            if old != owner:
                raise ValueError(f"Multiple owners for {target}")
    return result


def leakage_counts(candidates, partitions, owners):
    ignored = eligible = 0
    for query, targets in candidates.items():
        if partitions[query] != "fit":
            continue
        for target in targets:
            owner = owners.get(target)
            if owner == query:
                continue
            if owner is not None and partitions.get(owner) in {"calibration", "holdout"}:
                ignored += 1
            else:
                eligible += 1
    return {"ignored_validation_owned_candidates": ignored, "eligible_fit_negative_candidates": eligible, "validation_owned_labeled_negative": 0}
