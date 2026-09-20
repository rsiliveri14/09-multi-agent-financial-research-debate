"""Single-agent RAG baseline used for cost/quality comparison."""

from __future__ import annotations

from domain.enums import AgentRole, Polarities
from domain.models import RetrievedChunk, SingleAgentAnswer
from services.claims import claim_from_fact
from services.facts import extract_facts
from services.validator import validate_claims


def run_single_agent(question: str, hits: list[RetrievedChunk]) -> SingleAgentAnswer:
    facts = extract_facts(hits)
    if not facts:
        return SingleAgentAnswer(
            answer="Insufficient evidence in the retrieved filings to answer this question.",
            abstained=True,
            confidence=0.1,
        )
    claims = [
        claim_from_fact(
            fact,
            role=AgentRole.SINGLE_AGENT,
            confidence=0.62,
            assumptions=[],
            counterarguments=[],
            claim_id=f"single-{index}",
        )
        for index, fact in enumerate(facts[:5], start=1)
    ]
    results = validate_claims(claims)
    by_id = {item.claim_id: item for item in results}
    for claim in claims:
        result = by_id.get(claim.id)
        if result:
            claim.supported = result.supported
            claim.validation_score = result.score
    supported = [claim for claim in claims if claim.supported is not False]
    if not supported:
        return SingleAgentAnswer(
            answer="Retrieved passages did not yield supported claims.",
            claims=claims,
            citations=[],
            abstained=True,
            confidence=0.15,
        )
    answer = " ".join(claim.text for claim in supported[:3])
    citations = [citation for claim in supported for citation in claim.citations]
    polarity_score = sum(
        claim.confidence
        if claim.polarity == Polarities.POSITIVE
        else -claim.confidence
        if claim.polarity == Polarities.NEGATIVE
        else 0
        for claim in supported
    )
    confidence = min(0.8, 0.4 + 0.1 * len(supported) + (0.05 if polarity_score else 0))
    return SingleAgentAnswer(
        answer=answer,
        claims=claims,
        citations=citations[:8],
        abstained=False,
        confidence=round(confidence, 3),
    )
