from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.enums import (
    AgentRole,
    AgreementStatus,
    DocumentType,
    Polarities,
    QuestionType,
    RetrievalMode,
    RunStatus,
    TerminalState,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


class Issuer(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    ticker: str
    cik: str


class Page(BaseModel):
    page: int
    section: str
    text: str


class Document(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    issuer: Issuer
    document_type: DocumentType
    reporting_period: str
    publication_date: date
    title: str
    source_url: str
    local_path: str = ""
    content_hash: str = ""
    retrieved_at: datetime | None = None
    pages: list[Page] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(f"[p.{page.page} {page.section}] {page.text}" for page in self.pages)


class Chunk(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    document_id: UUID
    issuer_ticker: str
    document_type: DocumentType
    reporting_period: str
    publication_date: date
    chunk_index: int
    text: str
    page: int
    section: str
    start_char: int
    end_char: int
    token_count: int
    source_url: str
    content_hash: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk: Chunk
    vector_score: float = 0.0
    lexical_score: float = 0.0
    fused_score: float = 0.0
    rerank_score: float = 0.0
    rank: int = 0


class Citation(BaseModel):
    document_id: UUID
    page: int
    section: str
    chunk_id: UUID
    source_url: str
    evidence_span: str
    support_score: float = 0.0
    issuer_ticker: str = ""
    document_type: str = ""
    reporting_period: str = ""
    publication_date: date | None = None


class Message(BaseModel):
    role: str
    content: str


class DebateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What were Apple total net sales in FY2024, and did Greater China grow?",
                    "issuer_tickers": ["AAPL"],
                    "include_single_agent": True,
                }
            ]
        }
    )
    question: str = Field(min_length=3, max_length=2000)
    issuer_tickers: list[str] = Field(default_factory=list)
    document_types: list[DocumentType] = Field(default_factory=list)
    as_of_date: date | None = None
    max_debate_rounds: int | None = Field(default=None, ge=0, le=4)
    include_single_agent: bool = True
    include_trace: bool = True
    retrieval_mode: RetrievalMode = RetrievalMode.HYBRID_RERANK

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("question must contain at least 3 characters")
        return cleaned

    @field_validator("issuer_tickers")
    @classmethod
    def normalize_tickers(cls, value: list[str]) -> list[str]:
        return [item.strip().upper() for item in value if item.strip()]


class ResearchPlan(BaseModel):
    question: str
    question_type: QuestionType
    tickers: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    periods: list[str] = Field(default_factory=list)
    agent_queries: dict[str, str] = Field(default_factory=dict)
    rationale: str = ""
    max_rounds: int = 2


class Claim(BaseModel):
    id: str
    agent_role: AgentRole
    topic_key: str
    text: str
    polarity: Polarities
    confidence: float = Field(ge=0.0, le=1.0)
    value: float | None = None
    unit: str | None = None
    ticker: str = ""
    period: str = ""
    metric: str = ""
    assumptions: list[str] = Field(default_factory=list)
    counterarguments: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    supported: bool | None = None
    validation_score: float = 0.0
    rejection_reason: str | None = None
    stale_source: bool = False


class SpecialistBrief(BaseModel):
    role: AgentRole
    stance: Polarities
    summary: str
    claims: list[Claim] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    counterarguments: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    tool_calls: int = 0
    latency_ms: int = 0
    token_input: int = 0
    token_output: int = 0
    estimated_cost_usd: float = 0.0


class DisagreementCell(BaseModel):
    topic_key: str
    metric: str
    ticker: str
    period: str
    status: AgreementStatus
    agreement_score: float
    values: dict[str, float | None] = Field(default_factory=dict)
    polarities: dict[str, Polarities] = Field(default_factory=dict)
    claim_ids: list[str] = Field(default_factory=list)
    notes: str = ""


class CriticFinding(BaseModel):
    claim_id: str
    agent_role: AgentRole
    severity: str
    attack: str
    recommendation: str


class ValidationResult(BaseModel):
    claim_id: str
    supported: bool
    score: float
    reason: str
    preferred_citation: Citation | None = None


class GraphNode(BaseModel):
    id: str
    kind: str
    label: str
    meta: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    kind: str
    label: str = ""


class ProvenanceGraph(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class SynthesisReport(BaseModel):
    headline: str
    executive_summary: str
    agreed_facts: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    material_risks: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = 0.0
    outcome: TerminalState = TerminalState.COMPLETED


class SingleAgentAnswer(BaseModel):
    answer: str
    claims: list[Claim] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    abstained: bool = False
    confidence: float = 0.0
    latency_ms: int = 0
    token_input: int = 0
    token_output: int = 0
    estimated_cost_usd: float = 0.0


class DebateMetrics(BaseModel):
    latency_ms: int = 0
    retrieval_latency_ms: int = 0
    specialist_latency_ms: int = 0
    token_input: int = 0
    token_output: int = 0
    estimated_cost_usd: float = 0.0
    specialist_diversity: float = 0.0
    unsupported_claim_rate: float = 0.0
    contradiction_count: int = 0
    redundant_tool_calls: int = 0
    debate_rounds: int = 0
    cache_hit: bool = False


class DebateResult(BaseModel):
    request_id: str
    status: RunStatus
    question: str
    plan: ResearchPlan
    briefs: list[SpecialistBrief] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    disagreement: list[DisagreementCell] = Field(default_factory=list)
    critic_findings: list[CriticFinding] = Field(default_factory=list)
    validations: list[ValidationResult] = Field(default_factory=list)
    synthesis: SynthesisReport
    graph: ProvenanceGraph
    single_agent: SingleAgentAnswer | None = None
    metrics: DebateMetrics
    model_provider: str = ""
    model_name: str = ""
    terminal_state: TerminalState = TerminalState.COMPLETED
    errors: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)


class RunEvent(BaseModel):
    seq: int
    event_type: str
    node: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class DebateRunRecord(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    request_id: str
    question: str
    status: RunStatus
    terminal_state: TerminalState
    result: DebateResult | None = None
    events: list[RunEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0
    model_provider: str = ""
    model_name: str = ""
    error: str | None = None
