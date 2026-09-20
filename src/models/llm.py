from __future__ import annotations

import json
import re
from typing import Any, Protocol

from pydantic import BaseModel

from config.settings import Settings
from domain.errors import ProviderOutageError, ProviderTimeoutError, RateLimitError
from domain.models import Message
from models.structured import bounded_repair, parse_structured


class LLMResponse(BaseModel):
    text: str
    parsed: dict[str, Any] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model: str = ""
    provider: str = ""


class LLMProvider(Protocol):
    name: str
    model: str

    async def generate(
        self,
        messages: list[Message],
        *,
        response_schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse: ...


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


class HeuristicLLMProvider:
    """Offline adapter: debate logic lives in Python specialists, not this prompt.

    The provider exists so business code never calls a vendor SDK directly.
    When specialists request structured JSON, it returns a schema-valid stub
    that the deterministic pipeline already computed and placed in the prompt.
    """

    name = "heuristic"
    model = "heuristic-debate"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings

    async def generate(
        self,
        messages: list[Message],
        *,
        response_schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        user = next((m.content for m in reversed(messages) if m.role == "user"), "")
        payload = _extract_json_block(user) or {"status": "ok", "notes": "heuristic provider"}
        text = json.dumps(payload)
        parsed: dict[str, Any] | None = payload
        if response_schema is not None:
            try:
                model = parse_structured(response_schema, payload)
            except Exception:
                model = bounded_repair(response_schema, payload, attempts=2)
            parsed = model.model_dump()
            text = model.model_dump_json()
        return LLMResponse(
            text=text,
            parsed=parsed,
            input_tokens=_estimate_tokens(" ".join(m.content for m in messages)),
            output_tokens=_estimate_tokens(text),
            estimated_cost_usd=0.0,
            model=self.model,
            provider=self.name,
        )


def _extract_json_block(text: str) -> dict[str, Any] | None:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if not match:
        match = re.search(r"(\{.*\})", text, re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


class OpenAILLMProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str, timeout: float, settings: Settings) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.settings = settings

    async def generate(
        self,
        messages: list[Message],
        *,
        response_schema: type[BaseModel] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        import httpx

        body: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if response_schema is not None:
            body["response_format"] = {"type": "json_object"}
            schema_hint = json.dumps(response_schema.model_json_schema())
            body["messages"] = [
                {"role": "system", "content": f"Return JSON matching this schema: {schema_hint}"},
                *body["messages"],
            ]
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=body,
                )
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError() from exc
        except httpx.HTTPError as exc:
            raise ProviderOutageError() from exc
        if response.status_code == 429:
            raise RateLimitError()
        if response.status_code >= 500:
            raise ProviderOutageError(f"Provider returned {response.status_code}")
        if response.status_code >= 400:
            raise ProviderOutageError(f"Provider request failed ({response.status_code})")
        payload = response.json()
        choice = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage") or {}
        input_tokens = int(usage.get("prompt_tokens") or _estimate_tokens(" ".join(m.content for m in messages)))
        output_tokens = int(usage.get("completion_tokens") or _estimate_tokens(choice))
        cost = input_tokens * self.settings.input_token_usd + output_tokens * self.settings.output_token_usd
        parsed: dict[str, Any] | None = None
        text = choice
        if response_schema is not None:
            model = parse_structured(response_schema, choice)
            parsed = model.model_dump()
            text = model.model_dump_json()
        return LLMResponse(
            text=text,
            parsed=parsed,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
            model=self.model,
            provider=self.name,
        )


def build_llm(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAILLMProvider(
            settings.openai_api_key,
            settings.openai_model,
            settings.openai_base_url,
            settings.llm_timeout_seconds,
            settings,
        )
    return HeuristicLLMProvider(settings)
