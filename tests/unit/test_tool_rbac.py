from domain.enums import AgentRole
from domain.errors import AuthorizationError, ToolFailureError
from tools.contracts import TOOL_PERMISSIONS, YoYInput


def test_every_specialist_may_retrieve_except_critic_roles():
    assert "retrieve_filings" in TOOL_PERMISSIONS[AgentRole.BULL]
    assert "yoy" in TOOL_PERMISSIONS[AgentRole.FINANCIAL]
    assert TOOL_PERMISSIONS[AgentRole.CRITIC] == set()
    assert TOOL_PERMISSIONS[AgentRole.SYNTHESIZER] == set()


def test_yoy_rejects_zero_prior(runtime):
    try:
        runtime.tools.yoy(AgentRole.FINANCIAL, YoYInput(current=10, prior=0))
        raised = False
    except ToolFailureError:
        raised = True
    assert raised


def test_evidence_cannot_call_yoy(runtime):
    try:
        runtime.tools.yoy(AgentRole.EVIDENCE, YoYInput(current=2, prior=1))
        raised = False
    except AuthorizationError:
        raised = True
    assert raised
