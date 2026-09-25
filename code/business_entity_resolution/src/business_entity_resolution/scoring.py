"""Transparent rules-only pair score."""
from .normalize import normalize, numbers, stripped, tokens, trigrams


def jaccard(left, right):
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right) if left and right else 0.0


def containment(left, right):
    return len(left & right) / min(len(left), len(right)) if left and right else 0.0


def score(query, target, block_hits):
    q_name, t_name = normalize(query["business_name"]), normalize(target["business_name"])
    q_tokens, t_tokens = set(tokens(query["business_name"])), set(tokens(target["business_name"]))
    q_address, t_address = set(tokens(query["business_address"])), set(tokens(target["business_address"]))
    q_numbers, t_numbers = numbers(query["business_address"]), numbers(target["business_address"])
    value = 0.30 if q_name and q_name == t_name else 0.0
    value += 0.17 if stripped(query["business_name"]) == stripped(target["business_name"]) else 0.0
    value += 0.18 * jaccard(q_tokens, t_tokens)
    value += 0.10 * containment(q_tokens, t_tokens)
    value += 0.10 * jaccard(trigrams(query["business_name"]), trigrams(target["business_name"]))
    value += 0.08 * jaccard(q_address, t_address)
    value += 0.05 * jaccard(q_numbers, t_numbers) if q_numbers and t_numbers else 0.0
    value += min(block_hits, 3) / 3 * 0.02
    return min(value, 1.0)
