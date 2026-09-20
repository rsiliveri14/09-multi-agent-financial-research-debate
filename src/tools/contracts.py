"""Typed tool contracts. Specialists may only call tools listed for their role."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from domain.enums import AgentRole, RetrievalMode
from domain.models import RetrievedChunk


class RetrieveInput(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    issuer_tickers: list[str] = Field(default_factory=list)
    document_types: list[str] = Field(default_factory=list)
    as_of: date | None = None
    top_k: int = Field(default=8, ge=1, le=30)
    mode: RetrievalMode = RetrievalMode.HYBRID_RERANK


class RetrieveOutput(BaseModel):
    hits: list[RetrievedChunk]
    latency_ms: int
    empty: bool


class YoYInput(BaseModel):
    current: float
    prior: float


class YoYOutput(BaseModel):
    change_pct: float
    direction: str


TOOL_PERMISSIONS: dict[AgentRole, set[str]] = {
    AgentRole.PLANNER: set(),
    AgentRole.BULL: {"retrieve_filings"},
    AgentRole.BEAR: {"retrieve_filings"},
    AgentRole.FINANCIAL: {"retrieve_filings", "yoy"},
    AgentRole.RISK: {"retrieve_filings"},
    AgentRole.EVIDENCE: {"retrieve_filings"},
    AgentRole.CRITIC: set(),
    AgentRole.VALIDATOR: set(),
    AgentRole.SYNTHESIZER: set(),
    AgentRole.SINGLE_AGENT: {"retrieve_filings"},
}
