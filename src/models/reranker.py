from __future__ import annotations

import re
from typing import Protocol

from config.settings import Settings
from domain.models import RetrievedChunk

_TOKEN = re.compile(r"[a-z0-9$%.\-]+", re.I)
_NUMBER = re.compile(r"\$?\d[\d,]*\.?\d*%?")


class Reranker(Protocol):
    name: str

    def rerank(self, query: str, items: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]: ...


class HeuristicReranker:
    """Lexical overlap + numeric agreement + metadata-aware scoring."""

    name = "heuristic"

    def rerank(self, query: str, items: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        q_tokens = set(_TOKEN.findall(query.lower()))
        q_numbers = set(_NUMBER.findall(query))
        query_l = query.lower()
        scored: list[RetrievedChunk] = []
        for item in items:
            text = item.chunk.text.lower()
            tokens = set(_TOKEN.findall(text))
            overlap = len(q_tokens & tokens) / max(1, len(q_tokens))
            numbers = set(_NUMBER.findall(item.chunk.text))
            number_hit = 0.2 if (q_numbers & numbers) else 0.0
            metric_words = ("sales", "revenue", "income", "margin", "eps", "deliver", "azure", "aws")
            if not q_numbers and numbers and any(word in query_l for word in metric_words):
                number_hit = 0.18
            ticker_bonus = 0.12 if item.chunk.issuer_ticker.lower() in query_l else 0.0
            period_bonus = 0.0
            period = item.chunk.reporting_period.lower()
            year = "".join(ch for ch in period if ch.isdigit())
            if period in query_l or (year and year in query_l):
                period_bonus = 0.12
            phrase_bonus = 0.0
            for phrase in (
                "net sales",
                "total net sales",
                "operating income",
                "data center revenue",
                "intelligent cloud",
                "greater china",
                "automotive gross margin",
            ):
                if phrase in query_l and phrase in text:
                    phrase_bonus += 0.2
            section = item.chunk.section.lower()
            section_bonus = 0.08 if section.startswith("md&a") else 0.0
            if "risk" in query_l and "risk" in section:
                section_bonus += 0.15
            score = (
                0.35 * overlap
                + 0.20 * item.fused_score
                + number_hit
                + ticker_bonus
                + period_bonus
                + phrase_bonus
                + section_bonus
            )
            scored.append(item.model_copy(update={"rerank_score": score}))
        scored.sort(key=lambda item: item.rerank_score, reverse=True)
        return [item.model_copy(update={"rank": idx + 1}) for idx, item in enumerate(scored[:top_k])]


class CrossEncoderReranker:
    name = "cross_encoder"

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, items: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        if not items:
            return []
        pairs = [(query, item.chunk.text) for item in items]
        scores = self.model.predict(pairs)
        updated = [
            item.model_copy(update={"rerank_score": float(score)}) for item, score in zip(items, scores, strict=False)
        ]
        updated.sort(key=lambda item: item.rerank_score, reverse=True)
        return [item.model_copy(update={"rank": idx + 1}) for idx, item in enumerate(updated[:top_k])]


def build_reranker(settings: Settings) -> Reranker:
    if settings.reranker_backend == "cross_encoder":
        try:
            return CrossEncoderReranker(settings.reranker_model)
        except Exception:
            return HeuristicReranker()
    return HeuristicReranker()
