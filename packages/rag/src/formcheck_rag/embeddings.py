"""Local 1536-d retrieval vectors used when no OpenAI key is configured."""

from __future__ import annotations

import hashlib
import math
import re

LOCAL_EMBEDDING_MODEL = "local-bow-1536"
DIMENSIONS = 1536
_TOKEN = re.compile(r"[a-z0-9_]+")


def embed_text(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    for token in _TOKEN.findall(text.lower()):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
