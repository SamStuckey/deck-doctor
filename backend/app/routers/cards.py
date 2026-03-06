import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Card, CardStatus
from app.schemas import CardOut, CardFixRequest
from app.pipeline.scryfall import lookup_card

router = APIRouter()

@router.get("/cards", response_model=list[CardOut])
def get_cards(db: Session = Depends(get_db)):
    return db.query(Card).order_by(Card.created_at.desc()).all()

@router.delete("/cards/{card_id}", status_code=204)
def delete_card(card_id: str, db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Card not found")
    db.delete(card)
    db.commit()

@router.patch("/cards/{card_id}/fix", response_model=CardOut)
def fix_card(card_id: str, body: CardFixRequest, db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if not card:
        raise HTTPException(404, "Card not found")

    scryfall = asyncio.run(lookup_card(body.name))
    if not scryfall:
        raise HTTPException(404, f"No Scryfall match for '{body.name}'")

    card.name = scryfall.name
    card.scryfall_id = scryfall.scryfall_id
    card.image_url = scryfall.image_url
    card.colors = json.dumps(scryfall.colors)
    card.color_identity = json.dumps(scryfall.color_identity)
    card.type_line = scryfall.type_line
    card.mana_cost = scryfall.mana_cost
    card.oracle_text = scryfall.oracle_text
    card.status = CardStatus.identified
    db.commit()
    db.refresh(card)
    return card
