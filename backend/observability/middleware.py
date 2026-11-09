import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from backend.observability.tracing import tracer

MAX_PAYLOAD_SIZE = 1024 * 1024  # 1 MB limit

class SecurityObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Size Limit
        content_length = request.headers.get('content-length')
        if content_length and int(content_length) > MAX_PAYLOAD_SIZE:
            return JSONResponse(status_code=413, content={"detail": "Payload too large"})

        correlation_id = request.headers.get("x-correlation-id", f"corr_{uuid.uuid4()}")
        request.state.correlation_id = correlation_id

        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            attributes={"correlation_id": correlation_id}
        ) as span:
            start_time = time.time()
            try:
                response = await call_next(request)

                # Attach correlation ID to response
                response.headers["x-correlation-id"] = correlation_id

                # Sanitize error headers/responses if necessary
                return response
            except Exception as e:
                # Catch unexpected internals and map to 500 without stack trace
                # span.record_exception(e) - REMOVED for security to prevent stack trace leaks
                span.set_attribute("error_class", type(e).__name__)
                return JSONResponse(
                    status_code=500,
                    content={"detail": "Internal Server Error", "correlation_id": correlation_id}
                )
