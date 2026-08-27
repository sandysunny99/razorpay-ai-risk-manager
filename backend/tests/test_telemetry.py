"""
OpenTelemetry Distributed Tracing Unit Tests
"""
import pytest

from app.core.telemetry import get_tracer, setup_telemetry, trace_span


def test_setup_telemetry_provider():
    """Verify setup_telemetry returns a valid TracerProvider."""
    provider = setup_telemetry()
    assert provider is not None


def test_get_tracer_returns_tracer():
    """Verify get_tracer returns a valid OpenTelemetry tracer."""
    tracer = get_tracer("test-tracer")
    assert tracer is not None


def test_trace_span_context_manager():
    """Verify trace_span creates a span with designated attributes."""
    attributes = {
        "transaction.id": "TXN-TEST-1234",
        "merchant.id": "MERCHANT_RAZORPAY_01",
        "risk_score": 85.5,
    }
    with trace_span("test.risk.evaluation", attributes) as span:
        assert span is not None
        # Span is recording within its active context
        assert span.is_recording()


def test_trace_span_handles_empty_attributes():
    """Verify trace_span functions cleanly when no attributes are passed."""
    with trace_span("test.simple.span") as span:
        assert span is not None
