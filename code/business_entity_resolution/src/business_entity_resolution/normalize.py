"""Conservative normalization and blocking keys."""
import hashlib
import re
import unicodedata

SUFFIXES = {"co", "company", "corp", "corporation", "inc", "incorporated", "llc", "llp", "limited", "ltd", "pvt", "private", "plc"}


def normalize(value):
    value = unicodedata.normalize("NFKC", value).casefold().replace("&", " and ")
    return " ".join("".join(char if char.isalnum() else " " for char in value).split())


def tokens(value):
    return tuple(normalize(value).split())


def stripped(value):
    return " ".join(token for token in tokens(value) if token not in SUFFIXES)


def trigrams(value):
    value = normalize(value).replace(" ", "_")
    if len(value) < 3:
        return {value} if value else set()
    return {value[index:index + 3] for index in range(len(value) - 2)}


def simhash(value):
    grams = trigrams(value)
    if not grams:
        return 0
    weights = [0] * 64
    for gram in grams:
        number = int.from_bytes(hashlib.blake2b(gram.encode(), digest_size=8).digest(), "big")
        for bit in range(64):
            weights[bit] += 1 if number & (1 << bit) else -1
    return sum(1 << bit for bit, weight in enumerate(weights) if weight >= 0)


def blocking_keys(name, address):
    name_norm = normalize(name)
    name_tokens = tokens(name)
    result = set()
    if name_norm:
        result.update((f"ne:{name_norm}", f"ns:{' '.join(sorted(name_tokens))}"))
    legal = stripped(name)
    if legal:
        result.add(f"nl:{legal}")
    for token in name_tokens:
        if len(token) >= 5:
            result.update((f"nt:{token}", f"np:{token[:4]}"))
    for token in tokens(address):
        if token.isdigit() and len(token) >= 3:
            result.add(f"ad:{token}")
        elif len(token) >= 5:
            result.update((f"at:{token}", f"ap:{token[:4]}"))
    signature = simhash(name_norm)
    for band in range(4):
        result.add(f"sh{band}:{(signature >> (band * 16)) & 0xffff:04x}")
    return result


def numbers(value):
    return set(re.findall(r"\d+", normalize(value)))
