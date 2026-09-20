"""Role-specific specialists. Each filters the same fact pool differently."""

from __future__ import annotations

from domain.enums import AgentRole, Polarities
from domain.models import RetrievedChunk, SpecialistBrief
from services.claims import claim_from_fact, stance_from_claims
from services.facts import ExtractedFact, contradictory_pairs, extract_facts


def _ranked(facts: list[ExtractedFact]) -> list[ExtractedFact]:
    def score(fact: ExtractedFact) -> float:
        base = abs(fact.yoy_change_pct or 0) / 100.0
        if fact.citation:
            base += fact.citation.support_score
        if fact.is_preliminary:
            base += 0.15
        if fact.is_risk:
            base += 0.1
        return base + (0.05 if fact.value is not None else 0.0)

    ranked = sorted(facts, key=score, reverse=True)
    unique: list[ExtractedFact] = []
    seen: set[str] = set()
    for fact in ranked:
        if fact.topic_key in seen:
            continue
        seen.add(fact.topic_key)
        unique.append(fact)
        if len(unique) >= 6:
            break
    return unique


def _brief(
    role: AgentRole,
    facts: list[ExtractedFact],
    *,
    assumptions: list[str],
    counterarguments: list[str],
    summary: str,
    hits: list[RetrievedChunk],
    confidence_boost: float = 0.0,
) -> SpecialistBrief:
    claims = []
    for index, fact in enumerate(facts, start=1):
        extra_conf = 0.08 if fact.document_type in {"10-K", "10-Q"} else 0.0
        confidence = min(0.95, 0.55 + extra_conf + confidence_boost + (0.05 if fact.value is not None else 0.0))
        claims.append(
            claim_from_fact(
                fact,
                role=role,
                confidence=confidence,
                assumptions=assumptions[:1],
                counterarguments=counterarguments[:1],
                claim_id=f"{role.value}-{index}",
            )
        )
    stance = stance_from_claims(claims)
    if not claims:
        stance = Polarities.NEUTRAL
        summary = summary or "No role-relevant evidence in the retrieved set."
        confidence = 0.15
    else:
        confidence = sum(claim.confidence for claim in claims) / len(claims)
    return SpecialistBrief(
        role=role,
        stance=stance,
        summary=summary,
        claims=claims,
        assumptions=assumptions,
        counterarguments=counterarguments,
        confidence=round(confidence, 3),
        retrieved_chunk_ids=[str(hit.chunk.id) for hit in hits],
        tool_calls=1,
    )


def run_bull(hits: list[RetrievedChunk], facts: list[ExtractedFact] | None = None) -> SpecialistBrief:
    facts = facts if facts is not None else extract_facts(hits)
    selected = [
        fact
        for fact in facts
        if (fact.polarity == Polarities.POSITIVE or (fact.yoy_change_pct is not None and fact.yoy_change_pct > 0))
        and not fact.is_risk
    ]
    selected = _ranked(selected)
    return _brief(
        AgentRole.BULL,
        selected,
        assumptions=[
            "Growth rates observed in the latest primary filing persist into the next period.",
            "Segment mix continues to favor the expanding lines cited.",
        ],
        counterarguments=[
            "Offsetting declines in other segments are outside this brief's mandate.",
            "Preliminary 8-K figures may later be revised in the 10-Q/10-K.",
        ],
        summary=_summarize("Bull case emphasizes expansion, mix shift, and record-scale lines.", selected),
        hits=hits,
        confidence_boost=0.05,
    )


def run_bear(hits: list[RetrievedChunk], facts: list[ExtractedFact] | None = None) -> SpecialistBrief:
    facts = facts if facts is not None else extract_facts(hits)
    selected = [
        fact
        for fact in facts
        if fact.polarity in {Polarities.NEGATIVE, Polarities.MIXED}
        or fact.is_risk
        or (fact.yoy_change_pct is not None and fact.yoy_change_pct < 0)
        or fact.is_preliminary
    ]
    selected = _ranked(selected)
    return _brief(
        AgentRole.BEAR,
        selected,
        assumptions=[
            "Negative segment trends and disclosed risks are more informative than headline totals.",
            "Unaudited 8-K figures may overstate or understate the eventual 10-Q.",
        ],
        counterarguments=[
            "Consolidated growth can coexist with the weak segments cited here.",
            "Risk-factor language is forward-looking and not a realized loss.",
        ],
        summary=_summarize("Bear case emphasizes declines, preliminary restatements, and disclosed risks.", selected),
        hits=hits,
        confidence_boost=0.02,
    )


def run_financial(hits: list[RetrievedChunk], facts: list[ExtractedFact] | None = None) -> SpecialistBrief:
    facts = facts if facts is not None else extract_facts(hits)
    selected = [fact for fact in facts if fact.value is not None]
    selected = _ranked(selected)
    return _brief(
        AgentRole.FINANCIAL,
        selected,
        assumptions=[
            "Figures are taken from the cited reporting period without FX or non-GAAP adjustment.",
            "Year-over-year percentages use the immediately preceding comparable period in the same filing.",
        ],
        counterarguments=[
            "8-K preliminary amounts should not be mixed with 10-Q audited amounts without a reconciliation.",
        ],
        summary=_summarize("Financial agent reports measured quantities and documented percentage changes.", selected),
        hits=hits,
        confidence_boost=0.08,
    )


def run_risk(hits: list[RetrievedChunk], facts: list[ExtractedFact] | None = None) -> SpecialistBrief:
    facts = facts if facts is not None else extract_facts(hits)
    selected = [
        fact
        for fact in facts
        if fact.is_risk
        or "risk" in fact.section.lower()
        or fact.metric
        in {
            "export_controls",
            "china_demand",
            "automotive_gross_margin",
        }
    ]
    if not selected:
        selected = [fact for fact in facts if fact.polarity == Polarities.NEGATIVE]
    selected = _ranked(selected)
    return _brief(
        AgentRole.RISK,
        selected,
        assumptions=[
            "Disclosed risk factors remain applicable through the as-of date of the filing.",
        ],
        counterarguments=[
            "A risk factor is not evidence that the adverse event occurred in the reported period.",
        ],
        summary=_summarize(
            "Risk agent isolates disclosed threats, concentration, and regulatory constraints.", selected
        ),
        hits=hits,
    )


def run_evidence(hits: list[RetrievedChunk], facts: list[ExtractedFact] | None = None) -> SpecialistBrief:
    facts = facts if facts is not None else extract_facts(hits)
    pairs = contradictory_pairs(facts)
    selected = _ranked(facts)
    extra_assumptions = ["Primary evidence is limited to the retrieved filing pages."]
    extra_counters = []
    if pairs:
        left, right = pairs[0]
        extra_counters.append(
            f"Conflicting values for {left.topic_key}: {left.value} ({left.document_type}) vs {right.value} ({right.document_type})."
        )
        for fact in (left, right):
            if fact.topic_key not in {item.topic_key for item in selected}:
                selected.append(fact)
    return _brief(
        AgentRole.EVIDENCE,
        selected[:6],
        assumptions=extra_assumptions,
        counterarguments=extra_counters
        or ["Absence of a metric in retrieved pages is not proof the issuer did not report it elsewhere."],
        summary=_summarize("Evidence agent inventories sourced facts and flags intra-corpus conflicts.", selected),
        hits=hits,
        confidence_boost=0.06,
    )


def _summarize(prefix: str, facts: list[ExtractedFact]) -> str:
    if not facts:
        return prefix + " No qualifying facts."
    heads = "; ".join(f"{fact.ticker} {fact.metric} {fact.period}" for fact in facts[:3])
    return f"{prefix} Top topics: {heads}."


SPECIALISTS = {
    AgentRole.BULL: run_bull,
    AgentRole.BEAR: run_bear,
    AgentRole.FINANCIAL: run_financial,
    AgentRole.RISK: run_risk,
    AgentRole.EVIDENCE: run_evidence,
}
