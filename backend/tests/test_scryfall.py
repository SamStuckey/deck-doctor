import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.pipeline.scryfall import lookup_card, ScryfallResult

@pytest.mark.asyncio
async def test_lookup_known_card():
    mock_response = {
        "id": "abc123",
        "name": "Lightning Bolt",
        "colors": ["R"],
        "color_identity": ["R"],
        "type_line": "Instant",
        "mana_cost": "{R}",
        "oracle_text": "Lightning Bolt deals 3 damage to any target.",
        "image_uris": {"normal": "https://cards.scryfall.io/normal/front/e/3/e3285e6b.jpg"},
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await lookup_card("Lightning Bolt")

    assert result is not None
    assert result.name == "Lightning Bolt"
    assert result.colors == ["R"]
    assert result.image_url == "https://cards.scryfall.io/normal/front/e/3/e3285e6b.jpg"

@pytest.mark.asyncio
async def test_lookup_unknown_card():
    mock_resp = MagicMock()
    mock_resp.status_code = 404

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await lookup_card("xyzzy not a card")

    assert result is None

@pytest.mark.asyncio
async def test_lookup_double_faced_card():
    """Double-faced cards store image_uris on card_faces[0], not top-level."""
    mock_response = {
        "id": "dfc123",
        "name": "Delver of Secrets // Insectile Aberration",
        "colors": ["U"],
        "color_identity": ["U"],
        "type_line": "Creature — Human Wizard // Creature — Human Insect",
        "mana_cost": "{U}",
        "oracle_text": "At the beginning of your upkeep...",
        "card_faces": [
            {
                "image_uris": {"normal": "https://cards.scryfall.io/normal/front/dfc.jpg"}
            }
        ],
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        result = await lookup_card("Delver of Secrets")

    assert result is not None
    assert result.image_url == "https://cards.scryfall.io/normal/front/dfc.jpg"
