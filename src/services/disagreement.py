"""Disagreement matrix over normalized topic keys."""

from __future__ import annotations

from collections import defaultdict

from domain.enums import AgreementStatus, Polarities
from domain.models import Claim, DisagreementCell

OPPOSING = {Polarities.POSITIVE, Polarities.NEGATIVE}


def build_disagreement(claims: list[Claim], rel_tol: float = 0.015) -> list[DisagreementCell]:
    by_topic: dict[str, list[Claim]] = defaultdict(list)
    for claim in claims:
        if claim.topic_key:
            by_topic[claim.topic_key].append(claim)
    cells: list[DisagreementCell] = []
    for topic, group in sorted(by_topic.items()):
        roles = {claim.agent_role.value for claim in group}
        values: dict[str, float | None] = {
            claim.agent_role.value: claim.value for claim in group if claim.value is not None
        }
        polarities = {claim.agent_role.value: claim.polarity for claim in group}
        numeric = [claim.value for claim in group if claim.value is not None]
        value_conflict = False
        if len(numeric) >= 2:
            peak, floor = max(numeric), min(numeric)
            denom = max(abs(peak), abs(floor), 1e-9)
            value_conflict = (peak - floor) / denom > rel_tol
        polarity_set = {claim.polarity for claim in group if claim.polarity in OPPOSING}
        polarity_conflict = Polarities.POSITIVE in polarity_set and Polarities.NEGATIVE in polarity_set
        missing = len(roles) == 1
        if value_conflict or polarity_conflict:
            status = AgreementStatus.DISAGREE
            score = 0.2 if value_conflict and polarity_conflict else 0.35
        elif missing:
            status = AgreementStatus.MISSING
            score = 0.5
        elif Polarities.MIXED in {claim.polarity for claim in group}:
            status = AgreementStatus.PARTIAL
            score = 0.65
        else:
            status = AgreementStatus.AGREE
            score = 0.9 if len(roles) >= 2 else 0.7
        sample = group[0]
        notes = []
        if value_conflict:
            notes.append("numeric values diverge beyond tolerance")
        if polarity_conflict:
            notes.append("bullish vs bearish polarity")
        if missing:
            notes.append("only one specialist addressed this topic")
        cells.append(
            DisagreementCell(
                topic_key=topic,
                metric=sample.metric,
                ticker=sample.ticker,
                period=sample.period,
                status=status,
                agreement_score=score,
                values=values,
                polarities=polarities,
                claim_ids=[claim.id for claim in group],
                notes="; ".join(notes),
            )
        )
    return cells


def contradiction_count(cells: list[DisagreementCell]) -> int:
    return sum(1 for cell in cells if cell.status == AgreementStatus.DISAGREE)
