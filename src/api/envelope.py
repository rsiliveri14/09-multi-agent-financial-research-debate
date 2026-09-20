from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class Envelope(BaseModel, Generic[T]):
    request_id: str
    status: str
    data: T | None = None
    errors: list[ApiError] = Field(default_factory=list)


def ok(request_id: str, data: Any, status: str = "completed") -> dict[str, Any]:
    return Envelope(request_id=request_id, status=status, data=data, errors=[]).model_dump()


def fail(
    request_id: str, code: str, message: str, *, status: str = "failed", details: dict | None = None
) -> dict[str, Any]:
    return Envelope(
        request_id=request_id,
        status=status,
        data=None,
        errors=[ApiError(code=code, message=message, details=details or {})],
    ).model_dump()
