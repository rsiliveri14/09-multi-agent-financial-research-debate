"""Claim construction, normalization, and provenance helpers."""

from __future__ import annotations

from domain.enums import AgentRole, Polarities
from domain.models import Claim, SpecialistBrief
from services.facts import ExtractedFact


def claim_from_fact(
    fact: ExtractedFact,
    *,
    role: AgentRole,
    confidence: float,
    assumptions: list[str] | None = None,
    counterarguments: list[str] | None = None,
    claim_id: str,
) -> Claim:
    citations = [fact.citation] if fact.citation else []
    return Claim(
        id=claim_id,
        agent_role=role,
        topic_key=fact.topic_key,
        text=fact.text,
        polarity=fact.polarity,
        confidence=max(0.0, min(1.0, confidence)),
        value=fact.value,
        unit=fact.unit,
        ticker=fact.ticker,
        period=fact.period,
        metric=fact.metric,
        assumptions=assumptions or [],
        counterarguments=counterarguments or [],
        citations=citations,
        stale_source=fact.is_preliminary,
    )


def normalize_claims(briefs: list[SpecialistBrief]) -> list[Claim]:
    claims: list[Claim] = []
    for brief in briefs:
        for claim in brief.claims:
            claims.append(
                claim.model_copy(
                    update={
                        "topic_key": claim.topic_key or f"{claim.ticker}.{claim.metric}.{claim.period}",
                        "ticker": claim.ticker.upper() if claim.ticker else claim.ticker,
                    }
                )
            )
    return claims


def unique_topics(claims: list[Claim]) -> list[str]:
    return sorted({claim.topic_key for claim in claims if claim.topic_key})


def specialist_diversity(briefs: list[SpecialistBrief]) -> float:
    """Jaccard-style diversity: unique topics per specialist vs union."""
    sets = [{claim.topic_key for claim in brief.claims} for brief in briefs if brief.claims]
    if len(sets) < 2:
        return 0.0
    union = set().union(*sets)
    if not union:
        return 0.0
    pairwise = []
    for i, left in enumerate(sets):
        for right in sets[i + 1 :]:
            inter = len(left & right)
            uni = len(left | right) or 1
            pairwise.append(1.0 - inter / uni)
    return sum(pairwise) / len(pairwise)


def stance_from_claims(claims: list[Claim]) -> Polarities:
    if not claims:
        return Polarities.NEUTRAL
    score = 0.0
    for claim in claims:
        if claim.polarity == Polarities.POSITIVE:
            score += claim.confidence
        elif claim.polarity == Polarities.NEGATIVE:
            score -= claim.confidence
        elif claim.polarity == Polarities.MIXED:
            score += 0.0
    if score > 0.35:
        return Polarities.POSITIVE
    if score < -0.35:
        return Polarities.NEGATIVE
    if any(claim.polarity == Polarities.MIXED for claim in claims):
        return Polarities.MIXED
    return Polarities.NEUTRAL
