from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models import CardStatus

class CardOut(BaseModel):
    id: str
    name: Optional[str]
    scryfall_id: Optional[str]
    image_url: Optional[str]
    colors: Optional[str]
    color_identity: Optional[str]
    type_line: Optional[str]
    mana_cost: Optional[str]
    oracle_text: Optional[str]
    status: CardStatus
    created_at: datetime
    source_image: str

    model_config = {"from_attributes": True}

class CardFixRequest(BaseModel):
    name: str
