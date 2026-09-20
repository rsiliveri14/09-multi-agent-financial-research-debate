from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

debate_runs = Counter("debate_runs_total", "Debate runs", ["status"])
debate_latency = Histogram(
    "debate_latency_seconds",
    "Debate latency",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20),
)
debate_cost = Histogram(
    "debate_estimated_cost_usd",
    "Estimated USD cost per debate",
    buckets=(0.0, 0.0001, 0.001, 0.01, 0.05, 0.1),
)
retrieval_latency = Histogram(
    "retrieval_latency_seconds",
    "Retrieval latency",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
)
token_usage = Counter("llm_tokens_total", "Token usage", ["direction"])
retrieval_cache_hits = Counter("retrieval_cache_hits_total", "Retriever cache hits")
retrieval_cache_misses = Counter("retrieval_cache_misses_total", "Retriever cache misses")


def observe_debate(status: str, latency_ms: int, cost: float) -> None:
    debate_latency.observe(latency_ms / 1000.0)
    debate_cost.observe(cost)


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
