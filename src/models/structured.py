from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError
from pydantic_core import PydanticUndefined

from domain.errors import ValidationAppError


def parse_structured(schema: type[BaseModel], payload: dict[str, Any] | str) -> BaseModel:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValidationAppError("structured output was not valid JSON", details={"error": str(exc)}) from exc
    try:
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise ValidationAppError(
            "structured output failed schema validation", details={"errors": exc.errors()}
        ) from exc


def bounded_repair(schema: type[BaseModel], payload: dict[str, Any], *, attempts: int = 2) -> BaseModel:
    last_error: Exception | None = None
    current = dict(payload)
    for _ in range(max(1, attempts)):
        try:
            return schema.model_validate(current)
        except ValidationError as exc:
            last_error = exc
            for error in exc.errors():
                loc = error.get("loc") or ()
                if not loc:
                    continue
                key = loc[0]
                if not isinstance(key, str):
                    continue
                field = schema.model_fields.get(key)
                if field is None:
                    continue
                default = field.default
                if default is not None and default is not PydanticUndefined:
                    current[key] = default
                    continue
                annotation = field.annotation
                if annotation is str:
                    current[key] = ""
                elif annotation is list or str(annotation).startswith("list"):
                    current[key] = []
                elif annotation is float:
                    current[key] = 0.0
                elif annotation is int:
                    current[key] = 0
                elif annotation is bool:
                    current[key] = False
    raise ValidationAppError(
        "structured output could not be repaired",
        details={"errors": getattr(last_error, "errors", lambda: [])()},
    )
