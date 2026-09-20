"""Evidence validator: numeric match, lexical support, document preference."""

from __future__ import annotations

import re

from domain.models import Claim, ValidationResult
from services.chunking import publication_rank
from services.lexical import tokenize

_NUMBER = re.compile(r"\$?\d[\d,]*\.?\d*")


def validate_claims(claims: list[Claim], min_overlap: float = 0.22) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for claim in claims:
        if not claim.citations:
            results.append(
                ValidationResult(
                    claim_id=claim.id,
                    supported=False,
                    score=0.0,
                    reason="No citation attached.",
                )
            )
            continue
        preferred = max(
            claim.citations,
            key=lambda citation: (
                publication_rank(citation.document_type),
                citation.publication_date or citation.reporting_period,
                citation.support_score,
            ),
        )
        span = preferred.evidence_span
        overlap = _overlap(claim.text, span)
        numeric_ok = _numbers_supported(claim, span)
        score = 0.6 * overlap + (0.4 if numeric_ok else 0.0)
        if claim.stale_source and preferred.document_type == "8-K":
            score *= 0.85
            reason_extra = " Source is a preliminary 8-K."
        else:
            reason_extra = ""
        supported = score >= min_overlap and (numeric_ok or claim.value is None)
        reason = f"overlap={overlap:.2f} numeric_match={numeric_ok} doc={preferred.document_type}." + reason_extra
        if not supported:
            reason = "Unsupported: " + reason
        results.append(
            ValidationResult(
                claim_id=claim.id,
                supported=supported,
                score=round(score, 3),
                reason=reason,
                preferred_citation=preferred,
            )
        )
    return results


def apply_validations(claims: list[Claim], results: list[ValidationResult]) -> list[Claim]:
    by_id = {item.claim_id: item for item in results}
    updated: list[Claim] = []
    for claim in claims:
        result = by_id.get(claim.id)
        if result is None:
            updated.append(claim)
            continue
        updated.append(
            claim.model_copy(
                update={
                    "supported": result.supported,
                    "validation_score": result.score,
                    "rejection_reason": None if result.supported else result.reason,
                }
            )
        )
    return updated


def unsupported_rate(claims: list[Claim]) -> float:
    if not claims:
        return 0.0
    flagged = [claim for claim in claims if claim.supported is False]
    return len(flagged) / len(claims)


def _overlap(claim_text: str, span: str) -> float:
    left = set(tokenize(claim_text))
    right = set(tokenize(span))
    if not left:
        return 0.0
    return len(left & right) / len(left)


def _numbers_supported(claim: Claim, span: str) -> bool:
    if claim.value is None:
        claim_numbers = _NUMBER.findall(claim.text)
        span_numbers = set(_NUMBER.findall(span))
        if not claim_numbers:
            return True
        return any(number in span_numbers for number in claim_numbers)
    span_values = []
    for raw in _NUMBER.findall(span):
        try:
            span_values.append(float(raw.replace(",", "").replace("$", "")))
        except ValueError:
            continue
    if not span_values:
        return False
    return any(
        abs(claim.value - value) / max(abs(claim.value), 1e-9) < 0.02 or abs(claim.value - value) < 0.05
        for value in span_values
    )
