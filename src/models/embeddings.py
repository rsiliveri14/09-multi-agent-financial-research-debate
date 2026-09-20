from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

import numpy as np

from config.settings import Settings

_TOKEN = re.compile(r"[a-z0-9$%.\-]+", re.I)


class EmbeddingProvider(Protocol):
    name: str
    dim: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbeddingProvider:
    """Deterministic hashed bag-of-words embeddings for local/offline use."""

    name = "hashing"

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _vector(self, text: str) -> list[float]:
        vec = np.zeros(self.dim, dtype=np.float64)
        tokens = _TOKEN.findall(text.lower())
        if not tokens:
            return vec.tolist()
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + math.log1p(len(token))
            if token[0].isdigit() or token.startswith("$"):
                weight *= 2.4
            vec[idx] += sign * weight
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]


class OpenAIEmbeddingProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, dim: int, base_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.dim = dim
        self.base_url = base_url

    async def embed(self, texts: list[str]) -> list[list[float]]:
        import httpx

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": texts},
            )
            response.raise_for_status()
            payload = response.json()
        return [item["embedding"] for item in payload["data"]]


def build_embedder(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_backend == "openai":
        if not settings.openai_api_key:
            return HashingEmbeddingProvider(settings.embedding_dim)
        return OpenAIEmbeddingProvider(
            settings.openai_api_key,
            settings.embedding_model,
            settings.embedding_dim,
            settings.openai_base_url,
        )
    if settings.embedding_backend == "sentence_transformers":
        try:
            from sentence_transformers import SentenceTransformer

            class SentenceTransformerEmbeddingProvider:
                name = "sentence_transformers"

                def __init__(self, model_name: str, dim: int) -> None:
                    self.model = SentenceTransformer(model_name)
                    self.dim = dim

                async def embed(self, texts: list[str]) -> list[list[float]]:
                    vectors = self.model.encode(texts, normalize_embeddings=True)
                    return [vector.tolist() for vector in vectors]

            return SentenceTransformerEmbeddingProvider(settings.embedding_model, settings.embedding_dim)
        except Exception:
            return HashingEmbeddingProvider(settings.embedding_dim)
    return HashingEmbeddingProvider(settings.embedding_dim)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
