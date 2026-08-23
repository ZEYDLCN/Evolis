"""Embedding generation.

Preferred model: a multilingual sentence-transformers model (e5/BGE-M3) so
Turkish and English entries land in the same space (see docs/ARCHITECTURE.md
section "Embedding Teknolojisi"). sentence-transformers is a heavy optional
dependency; when it isn't installed we fall back to a cheap deterministic
hashing embedding so clustering/similarity code still has *something* to
operate on in dev/test environments.
"""
from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from typing import Protocol

DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
EMBEDDING_DIM = 1024


class EmbeddingModel(Protocol):
    name: str

    def embed(self, text: str) -> list[float]: ...


class SentenceTransformerEmbedding:
    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        from sentence_transformers import SentenceTransformer  # optional dep

        self.name = model_name
        self._model = SentenceTransformer(model_name)

    def embed(self, text: str) -> list[float]:
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()


class HashingEmbedding:
    """Deterministic, dependency-free stand-in for local dev and tests.

    NOT semantically meaningful beyond exact/near-duplicate text — it exists
    purely so the rest of the pipeline (storage, similarity plumbing,
    clustering interfaces) can be exercised without a multi-GB model
    download.
    """

    name = "hashing-fallback-v1"

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * EMBEDDING_DIM
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(0, len(digest), 4):
                idx = int.from_bytes(digest[i : i + 4], "big") % EMBEDDING_DIM
                vector[idx] += 1.0
        norm = sum(v * v for v in vector) ** 0.5 or 1.0
        return [v / norm for v in vector]


@lru_cache(maxsize=1)
def get_embedding_model() -> EmbeddingModel:
    try:
        return SentenceTransformerEmbedding()
    except Exception:
        return HashingEmbedding()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
