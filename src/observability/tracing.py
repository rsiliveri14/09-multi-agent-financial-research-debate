from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

from config.settings import Settings

_PROVIDER: TracerProvider | None = None


def configure_tracing(settings: Settings) -> None:
    global _PROVIDER
    if _PROVIDER is not None:
        return
    resource = Resource.create({"service.name": settings.otel_service_name})
    provider = TracerProvider(resource=resource)
    if settings.otel_console:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    if settings.otel_exporter_otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint))
            )
        except Exception:
            pass
    trace.set_tracer_provider(provider)
    _PROVIDER = provider


def get_tracer():
    return trace.get_tracer("financial-research-debate")


@contextmanager
def traced(name: str, **attributes: Any) -> Iterator[Any]:
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            if value is None:
                continue
            span.set_attribute(key, value if isinstance(value, (str, int, float, bool)) else str(value))
        yield span
