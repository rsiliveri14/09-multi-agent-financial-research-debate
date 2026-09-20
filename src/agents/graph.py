"""LangGraph wiring. Business logic lives in services/, not in graph nodes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agents.state import DebateState

NodeFn = Callable[[DebateState], DebateState]


def compile_debate_graph(nodes: dict[str, NodeFn]) -> Any:
    try:
        from langgraph.graph import END, StateGraph
    except Exception:
        return SequentialGraph(nodes)

    graph = StateGraph(DebateState)
    for name, fn in nodes.items():
        graph.add_node(name, fn)  # type: ignore[call-overload]
    graph.set_entry_point("plan")
    graph.add_edge("plan", "retrieve")
    graph.add_edge("retrieve", "specialists")
    graph.add_edge("specialists", "normalize")
    graph.add_edge("normalize", "disagreement")
    graph.add_edge("disagreement", "critic")
    graph.add_edge("critic", "validate")
    graph.add_conditional_edges("validate", _should_resolve, {"resolve": "resolve", "synthesize": "synthesize"})
    graph.add_edge("resolve", "synthesize")
    graph.add_edge("synthesize", END)
    return graph.compile()


def _should_resolve(state: DebateState) -> str:
    unresolved = state.get("unresolved") or []
    iteration = int(state.get("iteration") or 0)
    if unresolved and iteration <= 1:
        return "resolve"
    return "synthesize"


class SequentialGraph:
    """Fallback runner used if LangGraph is unavailable."""

    def __init__(self, nodes: dict[str, NodeFn]) -> None:
        self.nodes = nodes

    async def ainvoke(self, state: DebateState) -> DebateState:
        order = ["plan", "retrieve", "specialists", "normalize", "disagreement", "critic", "validate"]
        current = state
        for name in order:
            current = self.nodes[name](current)
        if _should_resolve(current) == "resolve":
            current = self.nodes["resolve"](current)
        return self.nodes["synthesize"](current)

    def invoke(self, state: DebateState) -> DebateState:
        import asyncio

        return asyncio.get_event_loop().run_until_complete(self.ainvoke(state))
