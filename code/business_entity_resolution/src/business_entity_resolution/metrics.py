"""Candidate and entity-level F0.5 metrics."""
import math
import statistics


def entity_f05(truth, prediction):
    if not truth:
        return 1.0 if not prediction else 0.0
    if not prediction:
        return 0.0
    true_positive = len(truth & prediction)
    if not true_positive:
        return 0.0
    precision = true_positive / len(prediction)
    recall = true_positive / len(truth)
    return 1.25 * precision * recall / (0.25 * precision + recall)


def macro_f05(truth, predictions, ids):
    return sum(entity_f05(truth[item], predictions.get(item, set())) for item in ids) / len(ids)


def percentile(values, probability):
    values = sorted(values)
    position = (len(values) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return float(values[lower])
    return values[lower] * (upper - position) + values[upper] * (position - lower)


def count_summary(values):
    return {"mean": statistics.fmean(values), "median": statistics.median(values), "p95": percentile(values, .95), "p99": percentile(values, .99), "max": max(values), "zero": values.count(0)}


def retrieval_metrics(truth, candidates, ids):
    total = sum(len(truth[item]) for item in ids)
    found = sum(len(truth[item] & candidates[item]) for item in ids)
    nonsingletons = [item for item in ids if truth[item]]
    complete = sum(truth[item] <= candidates[item] for item in nonsingletons)
    return {"true_links": total, "retrieved_links": found, "link_recall": found / total if total else 1.0, "non_singletons": len(nonsingletons), "complete_s1": complete, "whole_truth_retention": complete / len(nonsingletons) if nonsingletons else 1.0}


def choose_threshold(scored, truth, ids):
    best = (-1.0, 0.0)
    for threshold in [index / 40 for index in range(4, 39)]:
        predictions = {item: {target for target, value in scored[item] if value >= threshold} for item in ids}
        metric = macro_f05(truth, predictions, ids)
        if metric > best[0] or (metric == best[0] and threshold > best[1]):
            best = (metric, threshold)
    return best[1], best[0]
