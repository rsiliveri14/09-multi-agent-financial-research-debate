from agents.policy import ExecutionPolicy
from config.settings import Settings
from domain.errors import LoopDetectedError


def test_policy_terminates_on_iteration_limit():
    settings = Settings(max_iterations=2, max_wall_clock_seconds=30, max_token_budget=10_000)
    policy = ExecutionPolicy(settings)
    policy.check()
    policy.check()
    try:
        policy.check()
        raised = False
    except LoopDetectedError:
        raised = True
    assert raised


def test_policy_token_budget():
    settings = Settings(max_iterations=50, max_token_budget=10)
    policy = ExecutionPolicy(settings)
    try:
        policy.check(tokens=11)
        raised = False
    except LoopDetectedError:
        raised = True
    assert raised
