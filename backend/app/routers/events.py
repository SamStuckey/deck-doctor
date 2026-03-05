import asyncio
import json
import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis

router = APIRouter()

@router.get("/events/{job_id}")
async def job_events(job_id: str):
    """SSE stream for a processing job. Yields card results as they complete."""
    async def event_generator():
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        pubsub = r.pubsub()
        await pubsub.subscribe(f"job:{job_id}")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    yield f"data: {message['data'].decode()}\n\n"
                    data = json.loads(message["data"])
                    if data.get("done"):
                        break
        finally:
            await pubsub.unsubscribe(f"job:{job_id}")
            await r.aclose()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
