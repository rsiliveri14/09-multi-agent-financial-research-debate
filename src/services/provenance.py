"""Provenance graph: agents, claims, evidence, contradictions."""

from __future__ import annotations

from domain.enums import AgreementStatus
from domain.models import (
    Claim,
    DisagreementCell,
    GraphEdge,
    GraphNode,
    ProvenanceGraph,
    SpecialistBrief,
    SynthesisReport,
)


def build_graph(
    briefs: list[SpecialistBrief],
    claims: list[Claim],
    cells: list[DisagreementCell],
    report: SynthesisReport,
) -> ProvenanceGraph:
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    nodes.append(GraphNode(id="question", kind="question", label="Question"))
    for brief in briefs:
        node_id = f"agent:{brief.role.value}"
        nodes.append(
            GraphNode(
                id=node_id,
                kind="agent",
                label=brief.role.value,
                meta={"stance": brief.stance.value, "confidence": brief.confidence},
            )
        )
        edges.append(GraphEdge(source="question", target=node_id, kind="plans"))
    evidence_ids: set[str] = set()
    for claim in claims:
        claim_id = f"claim:{claim.id}"
        nodes.append(
            GraphNode(
                id=claim_id,
                kind="claim",
                label=claim.topic_key,
                meta={
                    "polarity": claim.polarity.value,
                    "supported": claim.supported,
                    "value": claim.value,
                },
            )
        )
        edges.append(GraphEdge(source=f"agent:{claim.agent_role.value}", target=claim_id, kind="asserts"))
        for citation in claim.citations:
            ev_id = f"evidence:{citation.chunk_id}"
            if ev_id not in evidence_ids:
                evidence_ids.add(ev_id)
                nodes.append(
                    GraphNode(
                        id=ev_id,
                        kind="evidence",
                        label=f"{citation.issuer_ticker} {citation.document_type} p.{citation.page}",
                        meta={
                            "section": citation.section,
                            "period": citation.reporting_period,
                            "url": citation.source_url,
                        },
                    )
                )
            edges.append(GraphEdge(source=claim_id, target=ev_id, kind="cites", label=citation.section))
    for cell in cells:
        if cell.status != AgreementStatus.DISAGREE:
            continue
        node_id = f"conflict:{cell.topic_key}"
        nodes.append(
            GraphNode(
                id=node_id,
                kind="contradiction",
                label=cell.topic_key,
                meta={"values": cell.values, "score": cell.agreement_score},
            )
        )
        for claim_id in cell.claim_ids:
            edges.append(GraphEdge(source=f"claim:{claim_id}", target=node_id, kind="conflicts"))
    nodes.append(
        GraphNode(
            id="synthesis",
            kind="synthesis",
            label=report.outcome.value,
            meta={"confidence": report.confidence},
        )
    )
    for brief in briefs:
        edges.append(GraphEdge(source=f"agent:{brief.role.value}", target="synthesis", kind="feeds"))
    return ProvenanceGraph(nodes=nodes, edges=edges)
