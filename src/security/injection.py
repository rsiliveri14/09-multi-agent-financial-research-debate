"""Treat retrieved filing text as untrusted data, never as instructions."""

from __future__ import annotations

INJECTION_MARKERS = (
    "ignore previous",
    "disregard your instructions",
    "system prompt",
    "tool call",
    "</untrusted",
)


def wrap_untrusted(text: str) -> str:
    cleaned = text.replace("</untrusted_evidence>", "")
    return f"<untrusted_evidence>\n{cleaned}\n</untrusted_evidence>"


def looks_like_injection(text: str) -> bool:
    lower = text.lower()
    return any(marker in lower for marker in INJECTION_MARKERS)
