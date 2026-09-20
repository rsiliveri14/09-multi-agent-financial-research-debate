from __future__ import annotations

from collections import defaultdict
from datetime import date
from time import perf_counter

from config.settings import Settings
from domain.enums import RetrievalMode
from domain.models import Chunk, RetrievedChunk
from models.embeddings import EmbeddingProvider, cosine_similarity
from models.reranker import Reranker
from observability.metrics import retrieval_cache_hits, retrieval_cache_misses, retrieval_latency
from services.lexical import BM25Index


class HybridRetriever:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        reranker: Reranker,
        settings: Settings,
    ) -> None:
        self.embedder = embedder
        self.reranker = reranker
        self.settings = settings
        self.chunks: list[Chunk] = []
        self.lexical = BM25Index()
        self._cache: dict[tuple[str, str, str, str, int], list[RetrievedChunk]] = {}

    def index(self, chunks: list[Chunk]) -> None:
        self.chunks = list(chunks)
        self.lexical.build(self.chunks)
        self._cache.clear()

    async def search(
        self,
        query: str,
        *,
        mode: RetrievalMode = RetrievalMode.HYBRID_RERANK,
        top_k: int | None = None,
        issuer_tickers: list[str] | None = None,
        document_types: list[str] | None = None,
        as_of: date | None = None,
    ) -> list[RetrievedChunk]:
        top_k = top_k or self.settings.retrieval_top_k
        cache_key = (
            query,
            mode.value,
            ",".join(sorted(issuer_tickers or [])),
            as_of.isoformat() if as_of else "",
            top_k,
        )
        cached = self._cache.get(cache_key)
        if cached is not None:
            retrieval_cache_hits.inc()
            return cached
        retrieval_cache_misses.inc()
        started = perf_counter()
        candidates = self._apply_filters(
            self.chunks,
            issuer_tickers=issuer_tickers,
            document_types=document_types,
            as_of=as_of,
        )
        if not candidates:
            self._cache[cache_key] = []
            return []
        lexical_hits: list[tuple[Chunk, float]] = []
        vector_hits: list[tuple[Chunk, float]] = []
        if mode in {RetrievalMode.LEXICAL, RetrievalMode.HYBRID, RetrievalMode.HYBRID_RERANK}:
            scoped = BM25Index()
            scoped.build(candidates)
            lexical_hits = scoped.search(query, top_k=top_k)
        if mode in {RetrievalMode.VECTOR, RetrievalMode.HYBRID, RetrievalMode.HYBRID_RERANK}:
            vector_hits = await self._vector_search(query, candidates, top_k)
        if mode == RetrievalMode.LEXICAL:
            fused = [
                RetrievedChunk(chunk=chunk, lexical_score=score, fused_score=score) for chunk, score in lexical_hits
            ]
        elif mode == RetrievalMode.VECTOR:
            fused = [RetrievedChunk(chunk=chunk, vector_score=score, fused_score=score) for chunk, score in vector_hits]
        else:
            fused = reciprocal_rank_fusion(
                lexical_hits,
                vector_hits,
                k=self.settings.rrf_k,
                lexical_weight=self.settings.hybrid_lexical_weight,
                vector_weight=self.settings.hybrid_vector_weight,
            )
        fused = fused[:top_k]
        if mode == RetrievalMode.HYBRID_RERANK:
            ranked = self.reranker.rerank(query, fused, self.settings.rerank_top_k)
        else:
            ranked = [item.model_copy(update={"rank": idx + 1}) for idx, item in enumerate(fused)]
        retrieval_latency.observe(perf_counter() - started)
        self._cache[cache_key] = ranked
        if len(self._cache) > 256:
            self._cache.pop(next(iter(self._cache)))
        return ranked

    async def _vector_search(self, query: str, candidates: list[Chunk], top_k: int) -> list[tuple[Chunk, float]]:
        query_vec = (await self.embedder.embed([query]))[0]
        scored: list[tuple[Chunk, float]] = []
        for chunk in candidates:
            if not chunk.embedding:
                continue
            scored.append((chunk, cosine_similarity(query_vec, chunk.embedding)))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def _apply_filters(
        self,
        chunks: list[Chunk],
        *,
        issuer_tickers: list[str] | None,
        document_types: list[str] | None,
        as_of: date | None,
    ) -> list[Chunk]:
        selected = chunks
        if issuer_tickers:
            tickers = {item.upper() for item in issuer_tickers}
            selected = [chunk for chunk in selected if chunk.issuer_ticker.upper() in tickers]
        if document_types:
            types = {item.upper() for item in document_types}
            selected = [chunk for chunk in selected if chunk.document_type.value.upper() in types]
        if as_of:
            selected = [chunk for chunk in selected if chunk.publication_date <= as_of]
        return selected


def reciprocal_rank_fusion(
    lexical_hits: list[tuple[Chunk, float]],
    vector_hits: list[tuple[Chunk, float]],
    *,
    k: int,
    lexical_weight: float,
    vector_weight: float,
) -> list[RetrievedChunk]:
    lexical_scores = {str(chunk.id): score for chunk, score in lexical_hits}
    vector_scores = {str(chunk.id): score for chunk, score in vector_hits}
    ranks: dict[str, float] = defaultdict(float)
    id_to_chunk: dict[str, Chunk] = {}
    for rank, (chunk, _) in enumerate(lexical_hits):
        key = str(chunk.id)
        id_to_chunk[key] = chunk
        ranks[key] += lexical_weight * (1.0 / (k + rank + 1))
    for rank, (chunk, _) in enumerate(vector_hits):
        key = str(chunk.id)
        id_to_chunk[key] = chunk
        ranks[key] += vector_weight * (1.0 / (k + rank + 1))
    fused = [
        RetrievedChunk(
            chunk=id_to_chunk[key],
            lexical_score=lexical_scores.get(key, 0.0),
            vector_score=vector_scores.get(key, 0.0),
            fused_score=score,
        )
        for key, score in ranks.items()
    ]
    return sorted(fused, key=lambda item: item.fused_score, reverse=True)
