from domain.models import DebateRequest
from services.facts import extract_facts
from services.planner import classify_question, detect_tickers, plan_research
from services.specialists import run_bear, run_bull, run_financial


def test_detect_tickers_from_names():
    assert detect_tickers("How did Apple Greater China perform versus Services?", []) == ["AAPL"]
    assert "MSFT" in detect_tickers("Microsoft Azure growth", [])
    assert detect_tickers("NVDA data center", ["nvda"]) == ["NVDA"]


def test_unanswerable_classification():
    from domain.enums import QuestionType

    assert (
        classify_question("What is Apple's FY2030 iPhone unit guidance versus Samsung market share?", ["AAPL"], [])
        == QuestionType.UNANSWERABLE
    )


def test_plan_includes_specialist_queries():
    plan = plan_research(DebateRequest(question="Did Tesla grow in 2024? Contrast automotive with energy."))
    assert plan.tickers == ["TSLA"]
    assert "bull" in plan.agent_queries
    assert "bear" in plan.agent_queries


async def test_bull_and_bear_select_different_facts(runtime):
    hits = await runtime.retriever.search("Apple Greater China net sales FY2024 decline growth")
    facts = extract_facts(hits)
    bull = run_bull(hits, facts)
    bear = run_bear(hits, facts)
    assert bull.claims
    assert bear.claims
    bull_keys = {claim.topic_key for claim in bull.claims}
    bear_keys = {claim.topic_key for claim in bear.claims}
    assert bull_keys != bear_keys or {claim.polarity for claim in bull.claims} != {
        claim.polarity for claim in bear.claims
    }


async def test_financial_emits_numeric_claims(runtime):
    hits = await runtime.retriever.search("Amazon AWS net sales 2024 107.6")
    brief = run_financial(hits)
    assert any(claim.value is not None for claim in brief.claims)
