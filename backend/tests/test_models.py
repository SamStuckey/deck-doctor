import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
from app.models import Card, CardStatus

def test_card_model_fields(db_session):
    card = Card(
        id="test-uuid-1",
        name="Lightning Bolt",
        scryfall_id="scry-123",
        image_url="https://example.com/img.jpg",
        colors='["R"]',
        color_identity='["R"]',
        type_line="Instant",
        mana_cost="{R}",
        oracle_text="Deal 3 damage.",
        status=CardStatus.identified,
        source_image="uploads/test.jpg",
    )
    db_session.add(card)
    db_session.commit()

    result = db_session.get(Card, "test-uuid-1")
    assert result.name == "Lightning Bolt"
    assert result.status == CardStatus.identified

def test_card_unidentified(db_session):
    card = Card(
        id="test-uuid-2",
        status=CardStatus.unidentified,
        source_image="uploads/test2.jpg",
    )
    db_session.add(card)
    db_session.commit()

    result = db_session.get(Card, "test-uuid-2")
    assert result.name is None
    assert result.image_url is None
