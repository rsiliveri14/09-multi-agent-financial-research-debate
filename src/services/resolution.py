"""Conflict resolution: return to primary evidence, prefer later periodic filings."""

from __future__ import annotations

from domain.enums import AgreementStatus, Polarities
from domain.models import Claim, DisagreementCell
from services.chunking import publication_rank


def resolve_conflicts(
    claims: list[Claim],
    cells: list[DisagreementCell],
) -> tuple[list[Claim], list[str], list[str]]:
    """Return updated claims, resolved topic keys, and still-unresolved keys.

    Resolution rule (deterministic):
    1. Prefer 10-K/10-Q over 8-K for the same ticker+metric+period.
    2. Prefer later publication_date among equal ranks.
    3. If remaining values still diverge, leave unresolved.
    """
    resolved: list[str] = []
    unresolved: list[str] = []
    winners: dict[str, Claim] = {}
    for cell in cells:
        if cell.status != AgreementStatus.DISAGREE:
            continue
        group = [claim for claim in claims if claim.id in cell.claim_ids]
        if not group:
            unresolved.append(cell.topic_key)
            continue
        ranked = sorted(
            group,
            key=lambda claim: _rank(claim),
            reverse=True,
        )
        winner = ranked[0]
        losers = ranked[1:]
        still_conflict = False
        for loser in losers:
            if winner.value is not None and loser.value is not None:
                denom = max(abs(winner.value), abs(loser.value), 1e-9)
                if abs(winner.value - loser.value) / denom > 0.015:
                    if _rank(loser) == _rank(winner):
                        still_conflict = True
        if still_conflict:
            unresolved.append(cell.topic_key)
            continue
        winners[cell.topic_key] = winner
        resolved.append(cell.topic_key)
        for loser in losers:
            loser.supported = False
            loser.rejection_reason = (
                f"Superseded by {winner.citations[0].document_type if winner.citations else 'primary'} "
                f"claim {winner.id}"
            )
            loser.counterarguments = list(loser.counterarguments) + [
                f"Primary-evidence resolution selected {winner.id}."
            ]
    return claims, resolved, unresolved


def _rank(claim: Claim) -> tuple[int, str, float, int]:
    citation = claim.citations[0] if claim.citations else None
    doc_type = citation.document_type if citation else ""
    published = str(citation.publication_date) if citation and citation.publication_date else ""
    support = citation.support_score if citation else 0.0
    periodic_bonus = 1 if not claim.stale_source else 0
    return (
        publication_rank(doc_type) + periodic_bonus,
        published,
        support,
        1 if claim.polarity != Polarities.MIXED else 0,
    )
