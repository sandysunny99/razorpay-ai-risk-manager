import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

provider = TracerProvider()
otel_mode = os.environ.get("OTEL_EXPORTER_MODE", "console")

if otel_mode == "console":
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
elif otel_mode == "otlp":
    # Production OTLP Exporter stub
    pass

# We also allow dynamically adding span processors for tests
def add_span_processor(proc):
    provider.add_span_processor(proc)

trace.set_tracer_provider(provider)
tracer = trace.get_tracer("netvrio.backend")
