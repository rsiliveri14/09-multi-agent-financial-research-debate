from agents.registry import NODE_CATALOG
from api.envelope import fail, ok
from security.auth import parse_bearer


def test_node_catalog_complete():
    expected = {
        "plan",
        "retrieve",
        "specialists",
        "normalize",
        "disagreement",
        "critic",
        "validate",
        "resolve",
        "synthesize",
    }
    assert expected <= set(NODE_CATALOG)
    for spec in NODE_CATALOG.values():
        assert spec["purpose"]
        assert spec["timeout_seconds"]


def test_envelope_ok_and_fail():
    payload = ok("req_1", {"hello": 1})
    assert payload["status"] == "completed"
    assert payload["data"]["hello"] == 1
    broken = fail("req_1", "NOT_FOUND", "missing")
    assert broken["errors"][0]["code"] == "NOT_FOUND"


def test_parse_bearer():
    assert parse_bearer("Bearer abc") == "abc"
    assert parse_bearer("bearer xyz") == "xyz"
    assert parse_bearer("Basic abc") is None
    assert parse_bearer(None) is None
