from domain.enums import AgentRole, Polarities
from domain.errors import (
    AuthenticationError,
    AuthorizationError,
    DatabaseFailureError,
    RateLimitError,
    ToolFailureError,
)
from domain.models import Claim
from services.disagreement import build_disagreement


def test_missing_and_partial_cells():
    claims = [
        Claim(
            id="only",
            agent_role=AgentRole.BULL,
            topic_key="AAPL.r_and_d.FY2024",
            text="R&D was $31.4 billion",
            polarity=Polarities.MIXED,
            confidence=0.5,
            value=31.4,
            ticker="AAPL",
            period="FY2024",
            metric="r_and_d",
        )
    ]
    cells = build_disagreement(claims)
    assert cells[0].status.value in {"missing", "partial"}


def test_more_error_codes():
    assert RateLimitError().http_status == 429
    assert DatabaseFailureError().http_status == 503
    assert ToolFailureError("x").http_status == 502
    assert AuthenticationError().code == "AUTHENTICATION_FAILURE"
    assert AuthorizationError().http_status == 403
