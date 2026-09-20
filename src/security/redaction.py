from __future__ import annotations

import re

_EMAIL = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE = re.compile(r"\b\+?\d[\d\- ]{8,}\d\b")
_KEY = re.compile(r"(sk-[A-Za-z0-9]{8,}|Bearer\s+[A-Za-z0-9\-._]+)", re.I)


def redact(text: str) -> str:
    redacted = _EMAIL.sub("[REDACTED_EMAIL]", text)
    redacted = _PHONE.sub("[REDACTED_PHONE]", redacted)
    redacted = _KEY.sub("[REDACTED_SECRET]", redacted)
    return redacted
