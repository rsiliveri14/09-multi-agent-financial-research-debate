from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from domain.models import Chunk

_TOKEN = re.compile(r"[a-z0-9$%.\-]+", re.I)
_SYNONYMS = {
    "revenues": "revenue",
    "revenue": "revenue",
    "sales": "sale",
    "sale": "sale",
    "earnings": "earning",
    "delivered": "deliver",
    "deliveries": "deliver",
    "delivery": "deliver",
    "margins": "margin",
}


def _normalize(token: str) -> str:
    token = token.lower()
    if token in _SYNONYMS:
        return _SYNONYMS[token]
    if token.endswith("es") and len(token) > 5:
        return token[:-2]
    if token.endswith("s") and len(token) > 4:
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    return [_normalize(token) for token in _TOKEN.findall(text) if token]


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.chunks: list[Chunk] = []
        self.doc_freq: dict[str, int] = defaultdict(int)
        self.doc_len: list[int] = []
        self.avgdl = 0.0
        self.inverted: dict[str, list[tuple[int, int]]] = defaultdict(list)

    def build(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.doc_freq.clear()
        self.doc_len = []
        self.inverted.clear()
        for idx, chunk in enumerate(chunks):
            tokens = tokenize(chunk.text)
            self.doc_len.append(len(tokens))
            counts = Counter(tokens)
            for token, tf in counts.items():
                self.doc_freq[token] += 1
                self.inverted[token].append((idx, tf))
        self.avgdl = (sum(self.doc_len) / len(self.doc_len)) if self.doc_len else 0.0

    def search(self, query: str, top_k: int = 20) -> list[tuple[Chunk, float]]:
        if not self.chunks:
            return []
        query_tokens = tokenize(query)
        scores: dict[int, float] = defaultdict(float)
        n = len(self.chunks)
        for token in query_tokens:
            postings = self.inverted.get(token)
            if not postings:
                continue
            df = self.doc_freq[token]
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            for idx, tf in postings:
                dl = self.doc_len[idx]
                denom = tf + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1.0))
                scores[idx] += idf * (tf * (self.k1 + 1)) / denom
        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        return [(self.chunks[idx], score) for idx, score in ranked]
