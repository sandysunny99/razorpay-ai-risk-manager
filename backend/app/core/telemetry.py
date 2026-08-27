"""
OpenTelemetry Distributed Tracing Setup
=========================================
Exports spans to OTLP endpoint if configured (e.g. Jaeger, Honeycomb, Datadog),
or provides graceful no-op / local trace provider for test & dev environments.
"""
from contextlib import contextmanager
import logging
import os
from typing import Any, Dict, Generator, Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

logger = logging.getLogger("telemetry")

_TRACER_INITIALIZED = False
_SERVICE_NAME = "razorpay-ai-risk-manager"


def setup_telemetry(app: Optional[FastAPI] = None) -> TracerProvider:
    """Initialize OpenTelemetry tracer provider and instrument FastAPI if passed."""
    global _TRACER_INITIALIZED
    if _TRACER_INITIALIZED:
        provider = trace.get_tracer_provider()
        if isinstance(provider, TracerProvider):
            return provider

    resource = Resource.create({SERVICE_NAME: _SERVICE_NAME})
    provider = TracerProvider(resource=resource)

    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )

            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OpenTelemetry initialized with OTLP endpoint: %s", otlp_endpoint)
        except Exception as exc:
            logger.warning("Failed to initialize OTLP exporter (%s), using SimpleProcessor", exc)
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    elif os.getenv("OTEL_DEBUG_CONSOLE", "false").lower() == "true":
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    _TRACER_INITIALIZED = True

    if app is not None:
        try:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
            logger.info("FastAPI successfully instrumented with OpenTelemetry.")
        except Exception as inst_exc:
            logger.debug("FastAPI instrumentation bypassed or already applied: %s", inst_exc)

    return provider


def get_tracer(name: str = "risk-manager") -> trace.Tracer:
    """Returns an OpenTelemetry tracer instance."""
    setup_telemetry()
    return trace.get_tracer(name)


@contextmanager
def trace_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> Generator[trace.Span, None, None]:
    """Context manager for convenient in-code span instrumentation."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, val in attributes.items():
                if val is not None:
                    span.set_attribute(key, str(val) if not isinstance(val, (int, float, bool)) else val)
        yield span
