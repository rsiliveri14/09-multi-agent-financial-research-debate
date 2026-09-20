"""Research planner: tickers, topics, question type, and specialist queries."""

from __future__ import annotations

import re

from data.corpus import ISSUERS
from domain.enums import AgentRole, QuestionType
from domain.models import DebateRequest, ResearchPlan

COMPANY_ALIASES = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "amazon": "AMZN",
    "nvidia": "NVDA",
    "tesla": "TSLA",
}

TOPIC_KEYWORDS = {
    "greater_china_sales": ("china", "greater china"),
    "iphone_sales": ("iphone",),
    "services_sales": ("services",),
    "azure_growth": ("azure", "intelligent cloud"),
    "aws_sales": ("aws",),
    "data_center_revenue": ("data center", "gpu", "hopper", "blackwell"),
    "gross_margin": ("gross margin", "margin"),
    "automotive_revenue": ("automotive", "vehicle"),
    "vehicle_deliveries": ("deliver", "delivery", "deliveries"),
    "export_controls": ("export", "restriction"),
    "net_sales": ("net sales", "revenue", "revenues"),
    "operating_income": ("operating income",),
    "net_income": ("net income", "earnings"),
    "eps": ("eps", "earnings per share"),
}

UNANSWERABLE_CUES = (
    "guidance for fy2030",
    "fy2030",
    "market share vs samsung",
    "samsung market share",
    "private company",
    "not in the corpus",
    "who is the ceo's spouse",
    "bitcoin treasury",
    "out of corpus",
)


def detect_tickers(question: str, requested: list[str]) -> list[str]:
    found: list[str] = []
    upper = question.upper()
    lower = question.lower()
    for ticker in ISSUERS:
        if re.search(rf"\b{ticker}\b", upper):
            found.append(ticker)
    for alias, ticker in COMPANY_ALIASES.items():
        if alias in lower and ticker not in found:
            found.append(ticker)
    for ticker in requested:
        symbol = ticker.upper()
        if symbol in ISSUERS and symbol not in found:
            found.append(symbol)
    return found


def detect_topics(question: str) -> list[str]:
    lower = question.lower()
    topics = [name for name, cues in TOPIC_KEYWORDS.items() if any(cue in lower for cue in cues)]
    if not topics:
        topics = ["net_sales", "net_income"]
    return topics


def detect_periods(question: str) -> list[str]:
    periods: list[str] = []
    lower = question.lower()
    for match in re.findall(r"fy\s?(20\d{2})", lower):
        periods.append(f"FY{match}")
    for match in re.findall(r"q([1-4])\s*(?:fy)?\s*(20\d{2})", lower):
        periods.append(f"Q{match[0]}FY{match[1]}")
    for year in re.findall(r"\b(20\d{2})\b", question):
        token = f"FY{year}"
        if token not in periods:
            periods.append(token)
    return periods


def classify_question(question: str, tickers: list[str], topics: list[str]) -> QuestionType:
    lower = question.lower()
    if any(cue in lower for cue in UNANSWERABLE_CUES) or "out of corpus" in lower:
        return QuestionType.UNANSWERABLE
    contradiction_cues = ("8-k", "preliminary", "versus the 10-q", "vs 10-q", "conflict", "contradict")
    if any(cue in lower for cue in contradiction_cues):
        return QuestionType.CONTRADICTORY
    if any(word in lower for word in ("compare", "versus", " vs ", "both", "and amazon", "and microsoft")):
        return QuestionType.COMPARISON
    if any(word in lower for word in ("trend", "since", "year over year", "yoy", "from 2023")):
        return QuestionType.TEMPORAL
    mixed_pairs = (("growth", "risk"), ("increase", "decline"), ("strength", "weak"), ("china", "services"))
    if any(left in lower and right in lower for left, right in mixed_pairs):
        return QuestionType.MIXED
    if len(topics) >= 3 or ("but" in lower or "despite" in lower):
        return QuestionType.MIXED
    if len(tickers) > 1:
        return QuestionType.COMPARISON
    return QuestionType.LOOKUP


def build_queries(question: str, tickers: list[str], topics: list[str]) -> dict[str, str]:
    focus = " ".join(tickers + topics)
    return {
        AgentRole.BULL.value: f"{question} {focus} growth increase record expansion higher",
        AgentRole.BEAR.value: f"{question} {focus} decline decrease risk weaker lower restriction",
        AgentRole.FINANCIAL.value: f"{question} {focus} revenue net income margin eps operating income",
        AgentRole.RISK.value: f"{question} {focus} risk factors export control regulatory cyclicality china",
        AgentRole.EVIDENCE.value: question,
        AgentRole.SINGLE_AGENT.value: question,
    }


def plan_research(request: DebateRequest) -> ResearchPlan:
    tickers = detect_tickers(request.question, request.issuer_tickers)
    topics = detect_topics(request.question)
    periods = detect_periods(request.question)
    question_type = classify_question(request.question, tickers, topics)
    queries = build_queries(request.question, tickers, topics)
    rationale = (
        f"Type={question_type.value}; tickers={tickers or ['unscoped']}; "
        f"topics={topics}; periods={periods or ['unspecified']}."
    )
    return ResearchPlan(
        question=request.question,
        question_type=question_type,
        tickers=tickers,
        topics=topics,
        periods=periods,
        agent_queries=queries,
        rationale=rationale,
        max_rounds=request.max_debate_rounds if request.max_debate_rounds is not None else 2,
    )
