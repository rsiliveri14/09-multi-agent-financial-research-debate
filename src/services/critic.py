"""Critic attacks unsupported assumptions, cherry-picking, and stale 8-Ks."""

from __future__ import annotations

from domain.enums import AgentRole, AgreementStatus
from domain.models import Claim, CriticFinding, DisagreementCell, SpecialistBrief
from services.lexical import tokenize


def critique(
    claims: list[Claim],
    briefs: list[SpecialistBrief],
    cells: list[DisagreementCell],
) -> list[CriticFinding]:
    findings: list[CriticFinding] = []
    disagree_topics = {cell.topic_key for cell in cells if cell.status == AgreementStatus.DISAGREE}
    bull_topics = {claim.topic_key for brief in briefs if brief.role == AgentRole.BULL for claim in brief.claims}
    bear_topics = {claim.topic_key for brief in briefs if brief.role == AgentRole.BEAR for claim in brief.claims}

    for claim in claims:
        if not claim.citations:
            findings.append(
                CriticFinding(
                    claim_id=claim.id,
                    agent_role=claim.agent_role,
                    severity="high",
                    attack="Claim has no citation to a filing page.",
                    recommendation="Drop the claim or retrieve a primary span.",
                )
            )
            continue
        span = " ".join(citation.evidence_span for citation in claim.citations)
        overlap = _overlap(claim.text, span)
        if overlap < 0.18:
            findings.append(
                CriticFinding(
                    claim_id=claim.id,
                    agent_role=claim.agent_role,
                    severity="high",
                    attack=f"Evidence overlap is {overlap:.2f}; the citation does not support the wording.",
                    recommendation="Rewrite from the evidence span or mark unsupported.",
                )
            )
        if claim.stale_source:
            findings.append(
                CriticFinding(
                    claim_id=claim.id,
                    agent_role=claim.agent_role,
                    severity="medium",
                    attack="Claim relies on a preliminary 8-K figure that a later 10-Q/10-K may supersede.",
                    recommendation="Prefer the later periodic report when both exist.",
                )
            )
        for assumption in claim.assumptions:
            if any(word in assumption.lower() for word in ("persist", "continue", "will", "next period")):
                findings.append(
                    CriticFinding(
                        claim_id=claim.id,
                        agent_role=claim.agent_role,
                        severity="medium",
                        attack=f"Forward-looking assumption is not in the filing: {assumption}",
                        recommendation="Keep the historical fact; do not project it.",
                    )
                )

    if bull_topics and bear_topics:
        ignored = bear_topics - bull_topics
        if ignored and any(brief.role == AgentRole.BULL for brief in briefs):
            findings.append(
                CriticFinding(
                    claim_id="bull-coverage",
                    agent_role=AgentRole.BULL,
                    severity="medium",
                    attack=f"Bull brief omitted negative topics raised by other specialists: {sorted(ignored)[:4]}",
                    recommendation="Acknowledge offsetting facts even when stance remains constructive.",
                )
            )
        ignored_pos = bull_topics - bear_topics
        if ignored_pos:
            findings.append(
                CriticFinding(
                    claim_id="bear-coverage",
                    agent_role=AgentRole.BEAR,
                    severity="low",
                    attack=f"Bear brief omitted expanding lines: {sorted(ignored_pos)[:4]}",
                    recommendation="State the offsetting growth so disagreement is scoped, not total.",
                )
            )

    for cell in cells:
        if cell.topic_key in disagree_topics and not cell.notes:
            findings.append(
                CriticFinding(
                    claim_id=cell.claim_ids[0] if cell.claim_ids else cell.topic_key,
                    agent_role=AgentRole.EVIDENCE,
                    severity="medium",
                    attack=f"Unresolved disagreement on {cell.topic_key} without a documented cause.",
                    recommendation="Return to primary evidence and compare document types and dates.",
                )
            )
    return _dedupe(findings)


def _overlap(claim_text: str, span: str) -> float:
    left = set(tokenize(claim_text))
    right = set(tokenize(span))
    if not left:
        return 0.0
    return len(left & right) / len(left)


def _dedupe(findings: list[CriticFinding]) -> list[CriticFinding]:
    seen: set[tuple[str, str]] = set()
    unique: list[CriticFinding] = []
    for finding in findings:
        key = (finding.claim_id, finding.attack)
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique
