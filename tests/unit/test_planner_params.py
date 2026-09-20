import pytest

from domain.enums import QuestionType
from domain.models import DebateRequest
from services.planner import classify_question, detect_periods, detect_tickers, detect_topics, plan_research


@pytest.mark.parametrize(
    "question,expected",
    [
        ("How did Apple Greater China perform?", ["AAPL"]),
        ("Microsoft Azure and Amazon AWS", ["MSFT", "AMZN"]),
        ("NVIDIA data center GPUs", ["NVDA"]),
        ("Tesla deliveries versus energy", ["TSLA"]),
        ("Compare AAPL and MSFT revenue", ["AAPL", "MSFT"]),
    ],
)
def test_detect_tickers_parametrized(question, expected):
    assert detect_tickers(question, []) == expected


@pytest.mark.parametrize(
    "question,expected",
    [
        ("Apple Q2 FY2025 8-K versus the 10-Q", QuestionType.CONTRADICTORY),
        ("Compare Microsoft and Amazon cloud", QuestionType.COMPARISON),
        ("NVIDIA revenue year over year since 2023", QuestionType.TEMPORAL),
        ("Apple FY2030 guidance versus Samsung market share", QuestionType.UNANSWERABLE),
        ("What were Amazon net sales in 2024?", QuestionType.LOOKUP),
        ("Tesla growth despite auto decline", QuestionType.MIXED),
    ],
)
def test_classify_question_types(question, expected):
    tickers = detect_tickers(question, [])
    topics = detect_topics(question)
    assert classify_question(question, tickers, topics) == expected


def test_detect_periods_and_topics():
    assert "FY2024" in detect_periods("Apple FY2024 net sales")
    assert "Q2FY2025" in detect_periods("Apple Q2 FY2025 results")
    topics = detect_topics("Greater China iPhone services")
    assert "greater_china_sales" in topics
    assert "iphone_sales" in topics


def test_plan_sets_max_rounds_from_request():
    plan = plan_research(DebateRequest(question="Amazon AWS 2024", max_debate_rounds=1))
    assert plan.max_rounds == 1
    assert plan.tickers == ["AMZN"]
    assert set(plan.agent_queries) >= {"bull", "bear", "financial", "risk", "evidence"}
