"""Real-time endpoints: Server-Sent Events feed, snapshot and live traffic generator controls."""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from backend.api.dependencies import get_tenant_auth_provider
from backend.realtime.bus import event_bus
from backend.realtime.generator import get_generator
from backend.runtime_env import demo_mode_enabled

router = APIRouter()

HEARTBEAT_SECONDS = 15.0


def get_stream_tenant(request: Request, tenant: Optional[str] = Query(default=None, max_length=100)) -> str:
    """Browsers' EventSource cannot set headers, so the demo tenant may also arrive as ?tenant=.

    The same auth provider is consulted first, so production mode still refuses (501) exactly as
    for every other endpoint; the query fallback only applies to the TEST provider.
    """
    provider = get_tenant_auth_provider()
    if request.headers.get("x-tenant-id") or not tenant:
        return provider.authenticate(request)
    if provider.__class__.__name__ != "TestTenantAuthProvider":
        return provider.authenticate(request)
    return tenant


def require_demo_mode() -> None:
    if not demo_mode_enabled():
        raise HTTPException(status_code=404, detail="Not Found")


def _sse(event: dict) -> str:
    return f"id: {event.get('seq', '')}\nevent: decision\ndata: {json.dumps(event, separators=(',', ':'), default=str)}\n\n"


@router.get("/events")
async def stream_events(request: Request, tenant_id: str = Depends(get_stream_tenant)):
    queue = event_bus.subscribe(tenant_id)

    async def body():
        try:
            yield "retry: 3000\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                    yield _sse(event)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            event_bus.unsubscribe(tenant_id, queue)

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.get("/snapshot")
def snapshot(limit: int = Query(default=200, ge=1, le=500), tenant_id: str = Depends(get_stream_tenant)):
    gen = get_generator(tenant_id).status() if demo_mode_enabled() else None
    return {
        "events": event_bus.recent(tenant_id, limit),
        "subscribers": event_bus.subscriber_count(tenant_id),
        "generator": gen,
    }


class GeneratorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    running: Optional[bool] = None
    rate_per_sec: Optional[float] = Field(default=None, ge=0.2, le=20.0)
    attack_ratio: Optional[float] = Field(default=None, ge=0.0, le=0.9)
    risky_ratio: Optional[float] = Field(default=None, ge=0.0, le=0.9)


@router.get("/generator")
def generator_status(tenant_id: str = Depends(get_stream_tenant), _: None = Depends(require_demo_mode)):
    return get_generator(tenant_id).status()


@router.post("/generator")
async def update_generator(
    update: GeneratorUpdate,
    tenant_id: str = Depends(get_stream_tenant),
    _: None = Depends(require_demo_mode),
):
    gen = get_generator(tenant_id)
    gen.configure(update.rate_per_sec, update.attack_ratio, update.risky_ratio)
    if update.running is True:
        gen.start()
    elif update.running is False:
        await gen.stop()
    return gen.status()
