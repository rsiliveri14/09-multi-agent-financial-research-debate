"""Synthesizer: evidence-first report. Unresolved disagreements stay unresolved."""

from __future__ import annotations

from domain.enums import AgreementStatus, Polarities, TerminalState
from domain.models import (
    Claim,
    CriticFinding,
    DisagreementCell,
    SpecialistBrief,
    SynthesisReport,
)


def synthesize(
    question: str,
    claims: list[Claim],
    cells: list[DisagreementCell],
    findings: list[CriticFinding],
    briefs: list[SpecialistBrief],
    unresolved_topics: list[str],
) -> SynthesisReport:
    supported = [claim for claim in claims if claim.supported is not False]
    agreed = [cell for cell in cells if cell.status == AgreementStatus.AGREE]
    disagreed = [cell for cell in cells if cell.status == AgreementStatus.DISAGREE]
    risk_claims = [
        claim
        for claim in supported
        if claim.agent_role.value == "risk" or claim.metric in {"export_controls", "china_demand"}
    ]
    citations = []
    seen = set()
    for claim in supported:
        for citation in claim.citations:
            key = (str(citation.chunk_id), citation.page)
            if key in seen:
                continue
            seen.add(key)
            citations.append(citation)

    agreed_facts = []
    for cell in agreed[:8]:
        sample = next((claim for claim in supported if claim.id in cell.claim_ids), None)
        if sample:
            agreed_facts.append(f"{sample.ticker} {sample.metric} {sample.period}: {sample.text}")

    unresolved = []
    for topic in unresolved_topics:
        match = next((item for item in disagreed if item.topic_key == topic), None)
        if match is None:
            unresolved.append(topic)
            continue
        unresolved.append(
            f"{match.topic_key}: values={match.values} polarities={ {k: v.value for k, v in match.polarities.items()} }. Left unresolved."
        )
    for cell in disagreed:
        if cell.topic_key not in unresolved_topics:
            continue

    material_risks = [claim.text for claim in risk_claims[:5]]
    high_findings = [item.attack for item in findings if item.severity == "high"][:3]

    if not supported:
        return SynthesisReport(
            headline="Insufficient evidence",
            executive_summary="Retrieved filings do not support a sourced answer. The system abstains rather than forcing consensus.",
            agreed_facts=[],
            unresolved=unresolved or ["No supported claims."],
            material_risks=material_risks,
            citations=citations,
            confidence=0.1,
            outcome=TerminalState.INSUFFICIENT_EVIDENCE,
        )

    stance = _overall_stance(supported)
    if unresolved_topics:
        outcome = TerminalState.UNRESOLVED
        headline = f"Mixed evidence with {len(unresolved_topics)} unresolved conflict(s)"
    else:
        outcome = TerminalState.COMPLETED
        headline = {
            Polarities.POSITIVE: "Evidence-supported constructive takeaways, with sourced caveats",
            Polarities.NEGATIVE: "Evidence-supported cautious takeaways",
            Polarities.MIXED: "Evidence is mixed across segments and periods",
            Polarities.NEUTRAL: "Factual readout without a directional stance",
        }[stance]

    summary_parts = [
        f"Question: {question.strip()}",
        f"Supported claims: {len(supported)} of {len(claims)}.",
        f"Agreed topics: {len(agreed)}; disagreed topics: {len(disagreed)}.",
    ]
    if agreed_facts:
        summary_parts.append("Agreed: " + agreed_facts[0])
    if unresolved:
        summary_parts.append("Unresolved items were not forced into consensus.")
    if high_findings:
        summary_parts.append("Critic: " + high_findings[0])
    confidence = _confidence(supported, unresolved_topics, briefs)

    return SynthesisReport(
        headline=headline,
        executive_summary=" ".join(summary_parts),
        agreed_facts=agreed_facts,
        unresolved=unresolved,
        material_risks=material_risks,
        citations=citations[:12],
        confidence=round(confidence, 3),
        outcome=outcome,
    )


def _overall_stance(claims: list[Claim]) -> Polarities:
    score = 0.0
    for claim in claims:
        weight = claim.confidence * (claim.validation_score or 0.5)
        if claim.polarity == Polarities.POSITIVE:
            score += weight
        elif claim.polarity == Polarities.NEGATIVE:
            score -= weight
    if score > 0.4:
        return Polarities.POSITIVE
    if score < -0.4:
        return Polarities.NEGATIVE
    return Polarities.MIXED


def _confidence(claims: list[Claim], unresolved: list[str], briefs: list[SpecialistBrief]) -> float:
    if not claims:
        return 0.1
    support = sum(1 for claim in claims if claim.supported) / max(1, len(claims))
    brief_conf = sum(brief.confidence for brief in briefs) / max(1, len(briefs))
    penalty = min(0.4, 0.08 * len(unresolved))
    return max(0.1, min(0.95, 0.5 * support + 0.5 * brief_conf - penalty))
