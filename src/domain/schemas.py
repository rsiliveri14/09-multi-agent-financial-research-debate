"""Typed input/output contracts for every workflow node."""

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.enums import AgentRole, Polarities, QuestionType
from domain.models import (
    Claim,
    CriticFinding,
    DisagreementCell,
    RetrievedChunk,
    SpecialistBrief,
    SynthesisReport,
    ValidationResult,
)


class PlannerInput(BaseModel):
    question: str
    issuer_tickers: list[str] = Field(default_factory=list)
    max_rounds: int = 2


class PlannerOutput(BaseModel):
    question_type: QuestionType
    tickers: list[str]
    topics: list[str]
    periods: list[str]
    agent_queries: dict[str, str]
    rationale: str


class SpecialistInput(BaseModel):
    role: AgentRole
    question: str
    query: str
    evidence: list[RetrievedChunk] = Field(default_factory=list)


class SpecialistOutput(BaseModel):
    brief: SpecialistBrief


class NormalizeInput(BaseModel):
    briefs: list[SpecialistBrief]


class NormalizeOutput(BaseModel):
    claims: list[Claim]
    topic_keys: list[str]


class DisagreementInput(BaseModel):
    claims: list[Claim]


class DisagreementOutput(BaseModel):
    cells: list[DisagreementCell]
    contradiction_count: int


class CriticInput(BaseModel):
    claims: list[Claim]
    briefs: list[SpecialistBrief]
    cells: list[DisagreementCell]


class CriticOutput(BaseModel):
    findings: list[CriticFinding]


class ValidatorInput(BaseModel):
    claims: list[Claim]


class ValidatorOutput(BaseModel):
    results: list[ValidationResult]
    claims: list[Claim]


class SynthesizerInput(BaseModel):
    question: str
    claims: list[Claim]
    cells: list[DisagreementCell]
    findings: list[CriticFinding]
    validations: list[ValidationResult]
    briefs: list[SpecialistBrief]


class SynthesizerOutput(BaseModel):
    report: SynthesisReport
    stance: Polarities = Polarities.MIXED
