from __future__ import annotations

from typing import Any

from domain.models import DebateResult


def numeric_accuracy(result: DebateResult, gold_facts: list[dict[str, Any]], rel_tol: float = 0.02) -> float:
    if not gold_facts:
        insufficient = (
            result.terminal_state.value == "insufficient_evidence"
            or result.synthesis.outcome.value == "insufficient_evidence"
        )
        return 1.0 if insufficient else 0.0
    hits = 0
    for fact in gold_facts:
        expected = fact.get("prefer", fact.get("value"))
        values = fact.get("values")
        topic = fact.get("topic", "")
        found = False
        for claim in result.claims:
            topic_ok = (
                not topic
                or claim.topic_key == topic
                or (bool(claim.ticker) and topic.startswith(claim.ticker) and claim.metric and claim.metric in topic)
            )
            if not topic_ok or claim.value is None:
                continue
            candidates = list(values) if values else [expected]
            for target in candidates:
                if target is None:
                    continue
                if abs(claim.value - float(target)) / max(abs(float(target)), 1e-9) <= rel_tol:
                    found = True
                    break
            if found:
                break
        if not found and expected is not None:
            blob = result.synthesis.executive_summary + " " + " ".join(claim.text for claim in result.claims)
            if number_in_text(float(expected), blob):
                found = True
        hits += int(found)
    return hits / len(gold_facts)


def number_in_text(value: float, text: str) -> bool:
    text = text.replace(",", "")
    as_int = f"{int(value)}" if value == int(value) else None
    as_float = f"{value:.1f}"
    return as_float in text or (as_int is not None and as_int in text)


def contradiction_detection_score(result: DebateResult, expected: bool) -> float:
    detected = result.metrics.contradiction_count > 0 or any(
        cell.status.value == "disagree" for cell in result.disagreement
    )
    if expected:
        return 1.0 if detected else 0.0
    return 1.0 if not detected else 0.6


def final_correctness(result: DebateResult, item: dict[str, Any]) -> float:
    if item.get("expect_insufficient"):
        return 1.0 if result.terminal_state.value == "insufficient_evidence" else 0.0
    acc = numeric_accuracy(result, item.get("gold_facts") or [])
    prefer = item.get("prefer_document")
    bonus = 0.0
    if prefer:
        cites = [citation.document_type for citation in result.synthesis.citations]
        if prefer in cites:
            bonus = 0.1
    return min(1.0, acc + bonus)


def score_run(result: DebateResult, item: dict[str, Any]) -> dict[str, Any]:
    supported_acc = numeric_accuracy(result, item.get("gold_facts") or [])
    return {
        "id": item["id"],
        "evidence_supported_accuracy": round(supported_acc, 3),
        "unsupported_claims": result.metrics.unsupported_claim_rate,
        "contradiction_detection": contradiction_detection_score(result, bool(item.get("expected_disagreement"))),
        "final_correctness": round(final_correctness(result, item), 3),
        "specialist_diversity": result.metrics.specialist_diversity,
        "redundant_tool_use": result.metrics.redundant_tool_calls,
        "latency_ms": result.metrics.latency_ms,
        "cost_usd": result.metrics.estimated_cost_usd,
        "single_agent_abstained": None if result.single_agent is None else result.single_agent.abstained,
        "single_agent_confidence": None if result.single_agent is None else result.single_agent.confidence,
        "terminal_state": result.terminal_state.value,
        "unresolved": len(result.synthesis.unresolved),
    }
