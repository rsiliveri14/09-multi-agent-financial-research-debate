"""Deterministic fact extraction from retrieved filing chunks.

Facts are the shared substrate. Specialists select and frame facts; they do not
invent numbers. Topic keys make disagreement measurable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from domain.enums import Polarities
from domain.models import Citation, RetrievedChunk

_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_NUMBER = re.compile(
    r"\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)\s*(billion|million|percent|%|vehicles|gwh)?",
    re.I,
)

POSITIVE_CUES = (
    "increase",
    "increased",
    "grew",
    "growth",
    "record",
    "expansion",
    "higher",
    "strong",
    "improved",
    "expansion",
    "productivity",
    "demand for",
)
NEGATIVE_CUES = (
    "decline",
    "declined",
    "decrease",
    "decreased",
    "weaker",
    "lower",
    "risk",
    "restriction",
    "compress",
    "compressed",
    "slowdown",
    "cautioned",
    "limit",
    "weaker than",
    "down from",
    "omit",
    "superseded",
    "unaudited",
    "subject to",
    "visibility was reduced",
    "inventory reserves",
)

METRIC_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("iphone_sales", ("iphone net sales",)),
    ("services_sales", ("services net sales",)),
    ("mac_sales", ("mac net sales",)),
    ("ipad_sales", ("ipad net sales",)),
    ("greater_china_sales", ("greater china net sales", "greater china quarterly net sales", "greater china remained")),
    ("americas_sales", ("americas net sales",)),
    ("europe_sales", ("europe net sales",)),
    ("aws_sales", ("aws net sales",)),
    ("aws_operating_income", ("aws operating income",)),
    ("intelligent_cloud_revenue", ("intelligent cloud revenue",)),
    ("azure_growth", ("azure and other cloud services",)),
    ("data_center_revenue", ("data center revenue",)),
    ("net_sales", ("total net sales", "net sales were", "total revenues were")),
    ("revenue", ("revenue was", "revenue for the", "revenue grew")),
    ("gaming_revenue", ("gaming revenue",)),
    ("networking_revenue", ("networking revenue",)),
    ("gross_margin", ("gross margin was", "gross margin")),
    ("automotive_revenue", ("automotive revenues",)),
    ("automotive_gross_margin", ("automotive gross margin",)),
    ("energy_revenue", ("energy generation and storage revenues", "energy storage")),
    (
        "vehicle_deliveries",
        ("deliveries were", "delivered", "delivery count", "preliminary deliveries", "the company delivered"),
    ),
    ("vehicle_production", ("produced", "preliminary first quarter 2025 production", "production of")),
    ("operating_income", ("operating income was", "operating income")),
    ("net_income", ("net income was", "net income attributable", "net income for")),
    ("eps", ("diluted earnings per share",)),
    ("r_and_d", ("research and development expense",)),
    ("cash", ("cash and cash equivalents", "cash, cash equivalents")),
    ("shareholder_returns", ("returned $", "share repurchases")),
    ("tax_rate", ("effective tax rate",)),
    ("export_controls", ("export control", "export control restrictions")),
    ("china_demand", ("greater china iphone", "greater china demand", "sell-through")),
    (
        "preliminary_results",
        ("preliminary net sales", "preliminary diluted", "preliminary deliveries", "preliminary first"),
    ),
    ("rpo", ("remaining performance obligation",)),
    ("azure_capacity", ("capacity expansion for azure",)),
]


@dataclass
class ExtractedFact:
    topic_key: str
    metric: str
    ticker: str
    period: str
    text: str
    value: float | None
    unit: str | None
    polarity: Polarities
    yoy_change_pct: float | None = None
    citation: Citation | None = None
    section: str = ""
    document_type: str = ""
    is_preliminary: bool = False
    is_risk: bool = False


def sentences(text: str) -> list[str]:
    parts = _SENTENCE.split(text.strip())
    return [part.strip() for part in parts if len(part.strip()) > 24]


def parse_number(raw: str) -> tuple[float | None, str | None]:
    match = _NUMBER.search(raw.replace("\u2011", "-"))
    if not match:
        return None, None
    amount = float(match.group(1).replace(",", ""))
    unit_raw = (match.group(2) or "").lower()
    if unit_raw in {"%", "percent"}:
        return amount, "percent"
    if unit_raw == "million":
        return amount / 1000.0, "billion"
    if unit_raw == "vehicles":
        return amount, "vehicles"
    if unit_raw == "gwh":
        return amount, "gwh"
    if unit_raw == "billion" or "$" in raw[: match.start() + 8]:
        return amount, "billion"
    if amount >= 1000:
        return amount, "count"
    return amount, None


def detect_polarity(text: str, yoy: float | None) -> Polarities:
    lower = text.lower()
    pos = sum(1 for cue in POSITIVE_CUES if cue in lower)
    neg = sum(1 for cue in NEGATIVE_CUES if cue in lower)
    if yoy is not None:
        if yoy > 1:
            pos += 1
        elif yoy < -1:
            neg += 1
    if pos and neg:
        return Polarities.MIXED
    if pos:
        return Polarities.POSITIVE
    if neg:
        return Polarities.NEGATIVE
    return Polarities.NEUTRAL


def detect_yoy(text: str) -> float | None:
    lower = text.lower()
    pct = re.search(r"(increase|decrease|grew|growth|down)\s+(?:of\s+)?(\d+(?:\.\d+)?)\s+percent", lower)
    if pct:
        value = float(pct.group(2))
        if pct.group(1) in {"decrease", "down"}:
            return -value
        return value
    compared = re.search(
        r"\$?([\d.]+)\s+billion.*?compared with\s+\$?([\d.]+)\s+billion",
        lower,
    )
    if compared:
        current = float(compared.group(1))
        prior = float(compared.group(2))
        if prior:
            return (current - prior) / prior * 100.0
    return None


def detect_metric(text: str) -> str | None:
    lower = text.lower()
    for metric, phrases in METRIC_PATTERNS:
        if any(phrase in lower for phrase in phrases):
            return metric
    return None


def topic_key(ticker: str, metric: str, period: str) -> str:
    return f"{ticker.upper()}.{metric}.{period}"


def citation_from_hit(hit: RetrievedChunk, span: str) -> Citation:
    chunk = hit.chunk
    return Citation(
        document_id=chunk.document_id,
        page=chunk.page,
        section=chunk.section,
        chunk_id=chunk.id,
        source_url=chunk.source_url,
        evidence_span=span[:400],
        support_score=max(hit.rerank_score, hit.fused_score),
        issuer_ticker=chunk.issuer_ticker,
        document_type=chunk.document_type.value,
        reporting_period=chunk.reporting_period,
        publication_date=chunk.publication_date,
    )


def extract_facts(hits: list[RetrievedChunk]) -> list[ExtractedFact]:
    facts: list[ExtractedFact] = []
    seen: set[str] = set()
    for hit in hits:
        chunk = hit.chunk
        for sentence in sentences(chunk.text):
            metric = detect_metric(sentence)
            if metric is None:
                continue
            value, unit = parse_number(sentence)
            yoy = detect_yoy(sentence)
            polarity = detect_polarity(sentence, yoy)
            period = chunk.reporting_period
            key = topic_key(chunk.issuer_ticker, metric, period)
            fingerprint = f"{key}|{sentence}"
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            lower = sentence.lower()
            facts.append(
                ExtractedFact(
                    topic_key=key,
                    metric=metric,
                    ticker=chunk.issuer_ticker,
                    period=period,
                    text=sentence.strip(),
                    value=value,
                    unit=unit,
                    polarity=polarity,
                    yoy_change_pct=yoy,
                    citation=citation_from_hit(hit, sentence.strip()),
                    section=chunk.section,
                    document_type=chunk.document_type.value,
                    is_preliminary="preliminary" in lower
                    or chunk.document_type.value == "8-K"
                    and metric
                    in {
                        "net_sales",
                        "eps",
                        "vehicle_deliveries",
                        "vehicle_production",
                        "preliminary_results",
                    },
                    is_risk="risk" in chunk.section.lower() or "export control" in lower or "cyclicality" in lower,
                )
            )
    return facts


def group_by_topic(facts: list[ExtractedFact]) -> dict[str, list[ExtractedFact]]:
    grouped: dict[str, list[ExtractedFact]] = {}
    for fact in facts:
        grouped.setdefault(fact.topic_key, []).append(fact)
    return grouped


def contradictory_pairs(facts: list[ExtractedFact], rel_tol: float = 0.01) -> list[tuple[ExtractedFact, ExtractedFact]]:
    pairs: list[tuple[ExtractedFact, ExtractedFact]] = []
    grouped = group_by_topic(facts)
    for items in grouped.values():
        numeric = [item for item in items if item.value is not None]
        for i, left in enumerate(numeric):
            for right in numeric[i + 1 :]:
                if left.unit != right.unit:
                    continue
                if left.value is None or right.value is None:
                    continue
                denom = max(abs(left.value), abs(right.value), 1e-9)
                if abs(left.value - right.value) / denom > rel_tol:
                    pairs.append((left, right))
        polarities = {item.polarity for item in items if item.polarity in {Polarities.POSITIVE, Polarities.NEGATIVE}}
        if Polarities.POSITIVE in polarities and Polarities.NEGATIVE in polarities:
            pos = next(item for item in items if item.polarity == Polarities.POSITIVE)
            neg = next(item for item in items if item.polarity == Polarities.NEGATIVE)
            if (pos, neg) not in pairs and (neg, pos) not in pairs:
                pairs.append((pos, neg))
    return pairs
