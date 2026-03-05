import pytest
import json
import numpy as np
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base
from app.models import Card, CardStatus

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_process_image_creates_identified_card(db, tmp_path):
    # Create a real small image file
    import cv2
    import numpy as np
    img = np.ones((100, 75, 3), dtype=np.uint8) * 128
    img_path = str(tmp_path / "test.jpg")
    cv2.imwrite(img_path, img)

    fake_crop = MagicMock()
    fake_crop.crop = img

    fake_scryfall = MagicMock()
    fake_scryfall.scryfall_id = "abc"
    fake_scryfall.name = "Lightning Bolt"
    fake_scryfall.colors = ["R"]
    fake_scryfall.color_identity = ["R"]
    fake_scryfall.type_line = "Instant"
    fake_scryfall.mana_cost = "{R}"
    fake_scryfall.oracle_text = "Deal 3 damage."
    fake_scryfall.image_url = "https://example.com/img.jpg"

    with patch("app.tasks.detect_cards", return_value=[fake_crop]), \
         patch("app.tasks.extract_title", return_value="Lightning Bolt"), \
         patch("app.tasks.asyncio.run", return_value=fake_scryfall), \
         patch("app.tasks.SessionLocal", return_value=db), \
         patch("app.tasks._publish_event"):

        from app.tasks import _process_image_sync
        cards = _process_image_sync(img_path, "job-1")

    assert len(cards) == 1
    assert cards[0].name == "Lightning Bolt"
    assert cards[0].status == CardStatus.identified

def test_process_image_unidentified_when_ocr_fails(db, tmp_path):
    import cv2
    import numpy as np
    img = np.ones((100, 75, 3), dtype=np.uint8) * 128
    img_path = str(tmp_path / "test2.jpg")
    cv2.imwrite(img_path, img)

    fake_crop = MagicMock()
    fake_crop.crop = img

    with patch("app.tasks.detect_cards", return_value=[fake_crop]), \
         patch("app.tasks.extract_title", return_value=None), \
         patch("app.tasks.SessionLocal", return_value=db), \
         patch("app.tasks._publish_event"):

        from app.tasks import _process_image_sync
        cards = _process_image_sync(img_path, "job-2")

    assert len(cards) == 1
    assert cards[0].status == CardStatus.unidentified
    assert cards[0].name is None

def test_process_image_returns_empty_for_unreadable_file():
    with patch("app.tasks._publish_event"):
        from app.tasks import _process_image_sync
        result = _process_image_sync("/nonexistent/path.jpg", "job-3")
    assert result == []
