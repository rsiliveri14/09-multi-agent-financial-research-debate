from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "financial-research-debate"
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8009
    cors_origins: str = "http://localhost:5179,http://127.0.0.1:5179,http://localhost:8090"

    store_backend: Literal["memory", "postgres"] = "memory"

    database_url: str = "postgresql+asyncpg://debate:debate@localhost:5439/debate"
    database_url_sync: str = "postgresql://debate:debate@localhost:5439/debate"
    redis_url: str = "redis://localhost:6389/0"

    api_tokens: str = "analyst:dev-analyst-token,admin:dev-admin-token"

    llm_provider: Literal["heuristic", "openai"] = "heuristic"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    llm_timeout_seconds: float = 20.0
    llm_max_repair_attempts: int = 2

    max_iterations: int = 12
    max_wall_clock_seconds: float = 45.0
    max_token_budget: int = 24000
    max_debate_rounds: int = 2
    tool_timeout_seconds: float = 6.0
    tool_max_retries: int = 2

    retrieval_top_k: int = 12
    rerank_top_k: int = 8
    rrf_k: int = 60
    hybrid_lexical_weight: float = 0.55
    hybrid_vector_weight: float = 0.45
    embedding_backend: Literal["hashing", "sentence_transformers", "openai"] = "hashing"
    embedding_dim: int = 384
    embedding_model: str = "text-embedding-3-small"
    reranker_backend: Literal["heuristic", "cross_encoder"] = "heuristic"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    input_token_usd: float = 0.00000015
    output_token_usd: float = 0.0000006

    circuit_failure_threshold: int = 5
    circuit_reset_seconds: float = 30.0

    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "financial-research-debate"
    otel_console: bool = False
    metrics_enabled: bool = True

    @field_validator("cors_origins")
    @classmethod
    def _strip_origins(cls, value: str) -> str:
        return value.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def token_role_map(self) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for pair in self.api_tokens.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            role, token = pair.split(":", 1)
            mapping[token.strip()] = role.strip().lower()
        return mapping


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
