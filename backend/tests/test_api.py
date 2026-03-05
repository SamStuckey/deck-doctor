import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, AsyncMock
from app.main import app
from app.database import Base, get_db
from app.models import Card, CardStatus

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)

@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_get_cards_empty(client):
    resp = client.get("/api/cards")
    assert resp.status_code == 200
    assert resp.json() == []

def test_get_cards_returns_list(client, db_session):
    card = Card(
        id="c1",
        name="Sol Ring",
        status=CardStatus.identified,
        source_image="uploads/test.jpg",
        colors='[]',
    )
    db_session.add(card)
    db_session.commit()

    resp = client.get("/api/cards")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Sol Ring"

def test_upload_no_files_returns_422(client):
    resp = client.post("/api/upload", data={})
    assert resp.status_code == 422

def test_fix_card_name(client, db_session):
    card = Card(id="c2", status=CardStatus.unidentified, source_image="uploads/test.jpg")
    db_session.add(card)
    db_session.commit()

    fake_scryfall = type("S", (), {
        "scryfall_id": "xyz", "name": "Black Lotus",
        "colors": [], "color_identity": [],
        "type_line": "Artifact", "mana_cost": "{0}",
        "oracle_text": "Sacrifice.", "image_url": "https://example.com/bl.jpg"
    })()

    with patch("app.routers.cards.lookup_card", new_callable=AsyncMock, return_value=fake_scryfall):
        resp = client.patch("/api/cards/c2/fix", json={"name": "Black Lotus"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "Black Lotus"
    assert resp.json()["status"] == "identified"

def test_fix_card_not_found(client):
    resp = client.patch("/api/cards/nonexistent/fix", json={"name": "Lightning Bolt"})
    assert resp.status_code == 404
