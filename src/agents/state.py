from __future__ import annotations

from typing import Any, TypedDict

from domain.models import (
    Claim,
    CriticFinding,
    DebateRequest,
    DisagreementCell,
    ResearchPlan,
    RetrievedChunk,
    SpecialistBrief,
    SynthesisReport,
    ValidationResult,
)


class DebateState(TypedDict, total=False):
    request: DebateRequest
    request_id: str
    plan: ResearchPlan
    evidence: dict[str, list[RetrievedChunk]]
    briefs: list[SpecialistBrief]
    claims: list[Claim]
    disagreement: list[DisagreementCell]
    critic_findings: list[CriticFinding]
    validations: list[ValidationResult]
    unresolved: list[str]
    resolved: list[str]
    report: SynthesisReport
    events: list[dict[str, Any]]
    errors: list[str]
    node: str
    iteration: int
