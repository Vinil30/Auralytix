import hashlib
import math
import re
from collections import Counter


EMBEDDING_DIMENSIONS = 384
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def generate_hash_embedding(text: str) -> list[float]:
    tokens = tokenize(text)

    if not tokens:
        return [0.0] * EMBEDDING_DIMENSIONS

    vector = [0.0] * EMBEDDING_DIMENSIONS

    for token, count in Counter(tokens).items():
        digest = hashlib.blake2b(
            token.encode("utf-8"),
            digest_size=8
        ).digest()
        bucket = int.from_bytes(digest[:4], "big") % EMBEDDING_DIMENSIONS
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[bucket] += sign * (1.0 + math.log(count))

    magnitude = math.sqrt(sum(value * value for value in vector))

    if magnitude == 0:
        return vector

    return [
        value / magnitude
        for value in vector
    ]
