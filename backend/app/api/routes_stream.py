# backend/app/api/routes_stream.py
"""
Phase 4 — Real-Time Risk Event Stream (Server-Sent Events)
===========================================================
SSE chosen over WebSocket because:
1. Unidirectional: server pushes events to client — perfect for risk alerts.
2. HTTP/1.1 compatible: no upgrade handshake, works through Cloudflare proxies.
3. Automatic reconnect: SSE has built-in browser reconnect semantics.

Multi-worker note: in single-worker demo mode this in-process queue works.
For production with gunicorn --workers 4, replace the asyncio.Queue with
a Redis pub/sub channel (see PHASE 6 architecture notes).
"""
import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

logger = logging.getLogger("risk_stream")

router = APIRouter(tags=["Real-Time Risk Stream"])

# ---------------------------------------------------------------------------
# In-process subscriber registry for SSE clients
# Each connected client gets its own asyncio.Queue entry.
# ---------------------------------------------------------------------------
_subscribers: list[asyncio.Queue] = []
_subscribers_lock = asyncio.Lock()


async def _register_subscriber() -> asyncio.Queue:
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    async with _subscribers_lock:
        _subscribers.append(queue)
    return queue


async def _unregister_subscriber(queue: asyncio.Queue) -> None:
    async with _subscribers_lock:
        try:
            _subscribers.remove(queue)
        except ValueError:
            pass


async def broadcast_risk_event(event_data: dict) -> None:
    """
    Called by EventBus subscribers or demo triggers to push events to all SSE clients.
    Non-blocking: drops event if a subscriber's queue is full (slow client).
    """
    payload = json.dumps(event_data, default=str)
    async with _subscribers_lock:
        dead = []
        for q in _subscribers:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                logger.warning("SSE subscriber queue full — dropping event for slow client.")
            except Exception as exc:
                logger.error(f"SSE broadcast error: {exc}")
                dead.append(q)
        for q in dead:
            _subscribers.remove(q)


async def _event_generator(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted data.
    Sends a heartbeat comment every 15 seconds to keep the connection alive
    through Cloudflare's 100-second idle timeout.
    """
    HEARTBEAT_INTERVAL = 15  # seconds

    try:
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_INTERVAL)
                yield f"data: {payload}\n\n"
            except asyncio.TimeoutError:
                # Heartbeat: SSE comment lines keep the TCP connection alive
                ts = datetime.now(timezone.utc).isoformat()
                yield f": heartbeat {ts}\n\n"
            except asyncio.CancelledError:
                break
    finally:
        await _unregister_subscriber(queue)


@router.get("/api/v1/stream/risk-events", summary="Real-time risk event SSE stream")
async def stream_risk_events() -> StreamingResponse:
    """
    Server-Sent Events endpoint for the Live Risk Screening dashboard.
    Connect with EventSource in the browser; events arrive as JSON payloads.

    Event format:
        data: {"event_type": "RISK_ALERT", "risk_score": 94.0, ...}

    The stream sends a heartbeat comment every 15 seconds when idle.
    """
    queue = await _register_subscriber()
    logger.info(f"New SSE subscriber connected. Total: {len(_subscribers)}")

    return StreamingResponse(
        _event_generator(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx/Cloudflare buffering
            "Connection": "keep-alive",
        },
    )
