"""Bounded execution policy. Termination does not depend on the LLM."""

from __future__ import annotations

import time

from config.settings import Settings
from domain.enums import TerminalState
from domain.errors import LoopDetectedError


class ExecutionPolicy:
    def __init__(self, settings: Settings, max_rounds: int | None = None) -> None:
        self.max_iterations = settings.max_iterations
        self.max_wall_clock_seconds = settings.max_wall_clock_seconds
        self.max_token_budget = settings.max_token_budget
        self.max_debate_rounds = max_rounds if max_rounds is not None else settings.max_debate_rounds
        self.tool_timeout_seconds = settings.tool_timeout_seconds
        self.tool_max_retries = settings.tool_max_retries
        self.started_at = time.monotonic()
        self.iterations = 0
        self.tokens = 0
        self.rounds = 0

    def remaining_seconds(self) -> float:
        return self.max_wall_clock_seconds - (time.monotonic() - self.started_at)

    def check(self, *, tokens: int = 0) -> None:
        self.iterations += 1
        self.tokens += tokens
        if self.iterations > self.max_iterations:
            raise LoopDetectedError("maximum iterations exceeded")
        if self.remaining_seconds() <= 0:
            raise LoopDetectedError("wall-clock budget exceeded")
        if self.tokens > self.max_token_budget:
            raise LoopDetectedError("token budget exceeded")

    def terminal_for_limit(self) -> TerminalState:
        if self.tokens > self.max_token_budget:
            return TerminalState.BUDGET_EXCEEDED
        return TerminalState.LOOP_DETECTED

    def can_debate_again(self) -> bool:
        return self.rounds < self.max_debate_rounds and self.remaining_seconds() > 1
