import asyncio
import json
import os
import uuid
import cv2
import numpy as np
import redis as _redis
from pathlib import Path

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Card, CardStatus
from app.pipeline.detect import detect_cards
from app.pipeline.ocr import extract_title
from app.pipeline.scryfall import lookup_card

def _get_redis_client() -> _redis.Redis:
    return _redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

def _publish_event(job_id: str, card: Card):
    """Publish a card result event to Redis for SSE streaming."""
    r = _get_redis_client()
    event_data = json.dumps({
        "card_id": card.id,
        "name": card.name,
        "status": card.status.value,
        "image_url": card.image_url,
    })
    r.publish(f"job:{job_id}", event_data)

def _process_image_sync(image_path: str, job_id: str) -> dict:
    img = cv2.imread(image_path)
    if img is None:
        return {"identified": 0, "unidentified": 0}

    regions = detect_cards(img)
    db = SessionLocal()
    identified = 0
    unidentified = 0

    try:
        for region in regions:
            card_id = str(uuid.uuid4())
            title = extract_title(region.crop)

            if title:
                # asyncio.run() is safe here because Celery uses prefork workers
                # (fully synchronous, no existing event loop in the thread).
                # If the worker pool is changed to gevent/eventlet, replace this
                # with a persistent event loop or a sync Scryfall client.
                scryfall = asyncio.run(lookup_card(title))
            else:
                scryfall = None

            if scryfall:
                card = Card(
                    id=card_id,
                    name=scryfall.name,
                    scryfall_id=scryfall.scryfall_id,
                    image_url=scryfall.image_url,
                    colors=json.dumps(scryfall.colors),
                    color_identity=json.dumps(scryfall.color_identity),
                    type_line=scryfall.type_line,
                    mana_cost=scryfall.mana_cost,
                    oracle_text=scryfall.oracle_text,
                    status=CardStatus.identified,
                    source_image=image_path,
                )
            else:
                card = Card(
                    id=card_id,
                    status=CardStatus.unidentified,
                    source_image=image_path,
                )

            db.add(card)
            db.commit()
            db.refresh(card)

            if card.status == CardStatus.identified:
                identified += 1
            else:
                unidentified += 1

            _publish_event(job_id, card)

    finally:
        db.close()

    return {"identified": identified, "unidentified": unidentified}

@celery_app.task(name="process_image")
def process_image(image_path: str, job_id: str):
    return _process_image_sync(image_path, job_id)
