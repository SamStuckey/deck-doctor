# Deck Doctor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web app where users photograph Magic: The Gathering card spreads, the app detects each card, reads its title via OCR, looks it up on Scryfall, and stores it in a browsable, searchable library.

**Architecture:** FastAPI backend with Celery workers processing images asynchronously (YOLOv8 detection → PaddleOCR title extraction → Scryfall lookup → SQLite storage). React/Vite frontend consumes REST + SSE endpoints. Docker Compose ties it all together.

**Tech Stack:** Python 3.11, FastAPI, Celery, Redis, SQLAlchemy, SQLite, Ultralytics YOLOv8, PaddleOCR, httpx, React 18, Vite, TypeScript, Tailwind CSS, fuse.js (fuzzy search), Docker Compose.

---

## Project Structure

```
deck_doctor/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app + routes
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── models.py          # Card ORM model
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── celery_app.py      # Celery instance
│   │   ├── tasks.py           # Celery tasks (pipeline)
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── detect.py      # YOLOv8 card detection
│   │   │   ├── ocr.py         # PaddleOCR title extraction
│   │   │   └── scryfall.py    # Scryfall API client
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── upload.py      # POST /api/upload
│   │       ├── cards.py       # GET /api/cards
│   │       └── events.py      # GET /api/events/{job_id}
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_detect.py
│   │   ├── test_ocr.py
│   │   ├── test_scryfall.py
│   │   ├── test_tasks.py
│   │   └── test_api.py
│   ├── uploads/               # uploaded images (gitignored)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── UploadZone.tsx
│   │   │   ├── ProgressFeed.tsx
│   │   │   ├── LibraryTileView.tsx
│   │   │   ├── LibraryGridView.tsx
│   │   │   ├── CardTile.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ColorFilter.tsx
│   │   │   ├── TypeFilter.tsx
│   │   │   └── FixCardModal.tsx
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx
│   │   │   └── LibraryPage.tsx
│   │   ├── hooks/
│   │   │   ├── useSSE.ts
│   │   │   └── useLibrary.ts
│   │   ├── api/
│   │   │   └── client.ts
│   │   └── types.ts
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docker-compose.yml
└── docs/
    └── plans/
```

---

## Task 1: Project Scaffolding & Docker Compose

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/tsconfig.json`
- Create: `docker-compose.yml`
- Create: `.gitignore`

**Step 1: Create backend/requirements.txt**

```text
fastapi==0.111.0
uvicorn[standard]==0.30.1
celery==5.4.0
redis==5.0.7
sqlalchemy==2.0.31
alembic==1.13.2
httpx==0.27.0
python-multipart==0.0.9
paddlepaddle==2.6.1
paddleocr==2.7.3
ultralytics==8.2.48
opencv-python-headless==4.10.0.84
Pillow==10.4.0
pytest==8.2.2
pytest-asyncio==0.23.7
httpx==0.27.0
```

**Step 2: Create backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**Step 3: Scaffold frontend with Vite**

```bash
cd frontend
npm create vite@latest . -- --template react-ts
npm install tailwindcss postcss autoprefixer fuse.js
npx tailwindcss init -p
```

**Step 4: Create docker-compose.yml**

```yaml
version: "3.9"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=sqlite:///./deck_doctor.db
    depends_on:
      - redis

  worker:
    build: ./backend
    command: celery -A app.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=sqlite:///./deck_doctor.db
    depends_on:
      - redis

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000

volumes:
  uploads:
```

**Step 5: Create .gitignore**

```
backend/uploads/
backend/*.db
backend/__pycache__/
backend/.pytest_cache/
frontend/node_modules/
frontend/dist/
.env
```

**Step 6: Commit**

```bash
git add .
git commit -m "chore: scaffold project structure and Docker Compose"
```

---

## Task 2: Database Models & SQLAlchemy Setup

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/database.py`
- Create: `backend/app/models.py`
- Create: `backend/app/schemas.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_models.py`

**Step 1: Write failing test**

```python
# backend/tests/test_models.py
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
```

**Step 2: Create conftest.py**

```python
# backend/tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    Base.metadata.drop_all(engine)
```

**Step 3: Run test to verify it fails**

```bash
cd backend
pytest tests/test_models.py -v
```
Expected: ImportError — modules don't exist yet.

**Step 4: Create backend/app/database.py**

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./deck_doctor.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 5: Create backend/app/models.py**

```python
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class CardStatus(str, enum.Enum):
    processing = "processing"
    identified = "identified"
    unidentified = "unidentified"

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    scryfall_id: Mapped[str | None] = mapped_column(String, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    colors: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array string
    color_identity: Mapped[str | None] = mapped_column(Text, nullable=True)
    type_line: Mapped[str | None] = mapped_column(Text, nullable=True)
    mana_cost: Mapped[str | None] = mapped_column(String, nullable=True)
    oracle_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CardStatus] = mapped_column(SAEnum(CardStatus), default=CardStatus.processing)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_image: Mapped[str] = mapped_column(String)
```

**Step 6: Create backend/app/schemas.py**

```python
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
```

**Step 7: Run tests to verify they pass**

```bash
cd backend
pytest tests/test_models.py -v
```
Expected: 2 passed.

**Step 8: Commit**

```bash
git add backend/app/ backend/tests/
git commit -m "feat: add database models and schemas"
```

---

## Task 3: Scryfall API Client

**Files:**
- Create: `backend/app/pipeline/__init__.py`
- Create: `backend/app/pipeline/scryfall.py`
- Create: `backend/tests/test_scryfall.py`

**Step 1: Write failing test**

```python
# backend/tests/test_scryfall.py
import pytest
from unittest.mock import AsyncMock, patch
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
        "image_uris": {"normal": "https://cards.scryfall.io/normal/front/e/3/e3285e6b-3e79-4d7c-bf96-d920f973b122.jpg"},
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        result = await lookup_card("Lightning Bolt")

    assert result is not None
    assert result.name == "Lightning Bolt"
    assert result.colors == ["R"]
    assert result.image_url is not None

@pytest.mark.asyncio
async def test_lookup_unknown_card():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 404
        result = await lookup_card("xyzzy not a card")

    assert result is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_scryfall.py -v
```
Expected: ImportError.

**Step 3: Create backend/app/pipeline/scryfall.py**

```python
import httpx
import asyncio
from dataclasses import dataclass
from typing import Optional

SCRYFALL_BASE = "https://api.scryfall.com"

@dataclass
class ScryfallResult:
    scryfall_id: str
    name: str
    colors: list[str]
    color_identity: list[str]
    type_line: str
    mana_cost: str
    oracle_text: str
    image_url: Optional[str]

async def lookup_card(name: str) -> Optional[ScryfallResult]:
    """Fuzzy-lookup a card by name on Scryfall. Returns None if not found."""
    await asyncio.sleep(0.1)  # respect Scryfall rate limit
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SCRYFALL_BASE}/cards/named",
            params={"fuzzy": name},
            timeout=10.0,
        )
    if resp.status_code != 200:
        return None

    data = resp.json()
    # Handle double-faced cards (image is on card_faces[0])
    image_uris = data.get("image_uris") or (
        data.get("card_faces", [{}])[0].get("image_uris", {})
    )
    return ScryfallResult(
        scryfall_id=data["id"],
        name=data["name"],
        colors=data.get("colors", []),
        color_identity=data.get("color_identity", []),
        type_line=data.get("type_line", ""),
        mana_cost=data.get("mana_cost", ""),
        oracle_text=data.get("oracle_text", ""),
        image_url=image_uris.get("normal"),
    )
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/test_scryfall.py -v
```
Expected: 2 passed.

**Step 5: Commit**

```bash
git add backend/app/pipeline/ backend/tests/test_scryfall.py
git commit -m "feat: add Scryfall API client"
```

---

## Task 4: Card Detection (YOLOv8 + OpenCV fallback)

**Files:**
- Create: `backend/app/pipeline/detect.py`
- Create: `backend/tests/test_detect.py`
- Create: `backend/tests/fixtures/single_card.jpg` (copy any test image)

**Step 1: Write failing tests**

```python
# backend/tests/test_detect.py
import numpy as np
import pytest
from app.pipeline.detect import detect_cards, CardRegion

def _make_white_image(h=600, w=450):
    return np.ones((h, w, 3), dtype=np.uint8) * 255

def test_detect_returns_list():
    img = _make_white_image()
    result = detect_cards(img)
    assert isinstance(result, list)

def test_card_region_has_crop():
    img = _make_white_image()
    # Inject a fake region directly
    region = CardRegion(crop=img[0:400, 0:300], bbox=(0, 0, 300, 400))
    assert region.crop.shape == (400, 300, 3)
    assert region.bbox == (0, 0, 300, 400)

def test_full_image_treated_as_single_card_when_no_detection():
    """If no cards detected, return the whole image as one region."""
    img = _make_white_image(100, 100)
    result = detect_cards(img, fallback_to_full_image=True)
    assert len(result) == 1
    assert result[0].crop.shape == img.shape
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_detect.py -v
```
Expected: ImportError.

**Step 3: Create backend/app/pipeline/detect.py**

```python
from dataclasses import dataclass
import numpy as np
import cv2
from typing import Optional

@dataclass
class CardRegion:
    crop: np.ndarray
    bbox: tuple[int, int, int, int]  # x1, y1, x2, y2

def _opencv_detect(img: np.ndarray) -> list[CardRegion]:
    """Fallback: find card-shaped rectangles via contour detection."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    regions = []
    ih, iw = img.shape[:2]
    min_area = (iw * ih) * 0.02  # ignore tiny blobs

    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        # MTG cards are ~2.5" x 3.5" — aspect ratio ~0.7
        aspect = w / h if h > 0 else 0
        if 0.5 < aspect < 0.9:
            pad = 4
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(iw, x + w + pad)
            y2 = min(ih, y + h + pad)
            regions.append(CardRegion(crop=img[y1:y2, x1:x2], bbox=(x1, y1, x2, y2)))

    return regions

def detect_cards(
    img: np.ndarray,
    fallback_to_full_image: bool = True,
    use_yolo: bool = True,
) -> list[CardRegion]:
    """
    Detect MTG card regions in an image.
    Tries YOLOv8 first, falls back to OpenCV contour detection,
    then falls back to full image if fallback_to_full_image=True.
    """
    regions: list[CardRegion] = []

    if use_yolo:
        try:
            from ultralytics import YOLO
            # Use general object detection — cards are rectangular objects
            # A fine-tuned model would be better, but this gives usable results
            model = YOLO("yolov8n.pt")  # downloaded on first run (~6MB)
            results = model(img, verbose=False)
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                crop = img[y1:y2, x1:x2]
                if crop.size > 0:
                    regions.append(CardRegion(crop=crop, bbox=(x1, y1, x2, y2)))
        except Exception:
            regions = []

    if not regions:
        regions = _opencv_detect(img)

    if not regions and fallback_to_full_image:
        h, w = img.shape[:2]
        regions = [CardRegion(crop=img.copy(), bbox=(0, 0, w, h))]

    return regions
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/test_detect.py -v
```
Expected: 3 passed.

**Step 5: Commit**

```bash
git add backend/app/pipeline/detect.py backend/tests/test_detect.py
git commit -m "feat: add YOLOv8 card detection with OpenCV fallback"
```

---

## Task 5: OCR — Title Extraction

**Files:**
- Create: `backend/app/pipeline/ocr.py`
- Create: `backend/tests/test_ocr.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_ocr.py
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from app.pipeline.ocr import extract_title, crop_title_region

def _make_card_image(h=600, w=450):
    return np.ones((h, w, 3), dtype=np.uint8) * 200

def test_crop_title_region_shape():
    img = _make_card_image(600, 450)
    region = crop_title_region(img)
    # Should be top ~12% of height, left ~70% of width
    assert region.shape[0] < 600 * 0.2
    assert region.shape[1] < 450 * 0.8

def test_extract_title_returns_string_or_none():
    img = _make_card_image()
    # With a blank image, OCR should return empty string or None — not crash
    result = extract_title(img)
    assert result is None or isinstance(result, str)

def test_extract_title_cleans_whitespace():
    img = _make_card_image()
    with patch("app.pipeline.ocr._run_paddleocr") as mock_ocr:
        mock_ocr.return_value = "  Lightning Bolt  \n"
        result = extract_title(img)
    assert result == "Lightning Bolt"

def test_extract_title_returns_none_on_empty():
    img = _make_card_image()
    with patch("app.pipeline.ocr._run_paddleocr") as mock_ocr:
        mock_ocr.return_value = ""
        result = extract_title(img)
    assert result is None
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_ocr.py -v
```
Expected: ImportError.

**Step 3: Create backend/app/pipeline/ocr.py**

```python
import numpy as np
import cv2
from typing import Optional

_paddle_ocr = None

def _get_ocr():
    global _paddle_ocr
    if _paddle_ocr is None:
        from paddleocr import PaddleOCR
        _paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _paddle_ocr

def crop_title_region(img: np.ndarray) -> np.ndarray:
    """
    Crop the title region from a card image.
    MTG card titles are in the top ~12% of the card, left ~72% of width
    (the right portion is the mana cost symbols).
    """
    h, w = img.shape[:2]
    y2 = int(h * 0.12)
    x2 = int(w * 0.72)
    return img[0:y2, 0:x2]

def _preprocess(img: np.ndarray) -> np.ndarray:
    """Enhance contrast for OCR accuracy."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # CLAHE for local contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    enhanced = clahe.apply(gray)
    # Scale up small images
    h, w = enhanced.shape[:2]
    if h < 40:
        scale = 40 / h
        enhanced = cv2.resize(enhanced, (int(w * scale), 40), interpolation=cv2.INTER_CUBIC)
    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)

def _run_paddleocr(img: np.ndarray) -> str:
    """Run PaddleOCR and return concatenated text."""
    ocr = _get_ocr()
    result = ocr.ocr(img, cls=True)
    if not result or not result[0]:
        return ""
    texts = [line[1][0] for line in result[0] if line and line[1]]
    return " ".join(texts)

def extract_title(card_img: np.ndarray) -> Optional[str]:
    """
    Extract the card title from a card image.
    Crops the title region, preprocesses, runs PaddleOCR.
    Returns cleaned title string, or None if nothing found.
    """
    region = crop_title_region(card_img)
    processed = _preprocess(region)
    raw = _run_paddleocr(processed)
    cleaned = raw.strip()
    return cleaned if cleaned else None
```

**Step 4: Run tests**

```bash
cd backend
pytest tests/test_ocr.py -v
```
Expected: 4 passed.

**Step 5: Commit**

```bash
git add backend/app/pipeline/ocr.py backend/tests/test_ocr.py
git commit -m "feat: add PaddleOCR title extraction"
```

---

## Task 6: Celery App & Processing Task

**Files:**
- Create: `backend/app/celery_app.py`
- Create: `backend/app/tasks.py`
- Create: `backend/tests/test_tasks.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_tasks.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
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

def test_process_image_creates_identified_card(db):
    import numpy as np

    fake_crop = np.ones((600, 450, 3), dtype=np.uint8) * 128
    fake_scryfall = MagicMock(
        scryfall_id="abc",
        name="Lightning Bolt",
        colors=["R"],
        color_identity=["R"],
        type_line="Instant",
        mana_cost="{R}",
        oracle_text="Deal 3 damage.",
        image_url="https://example.com/img.jpg",
    )

    with patch("app.tasks.detect_cards") as mock_detect, \
         patch("app.tasks.extract_title", return_value="Lightning Bolt"), \
         patch("app.tasks.asyncio.run", return_value=fake_scryfall), \
         patch("app.tasks.SessionLocal", return_value=db):

        mock_detect.return_value = [MagicMock(crop=fake_crop)]

        from app.tasks import _process_image_sync
        cards = _process_image_sync("uploads/test.jpg", "job-1")

    assert len(cards) >= 1

def test_process_image_creates_unidentified_card_on_ocr_failure(db):
    import numpy as np

    fake_crop = np.ones((600, 450, 3), dtype=np.uint8) * 128

    with patch("app.tasks.detect_cards") as mock_detect, \
         patch("app.tasks.extract_title", return_value=None), \
         patch("app.tasks.SessionLocal", return_value=db):

        mock_detect.return_value = [MagicMock(crop=fake_crop)]

        from app.tasks import _process_image_sync
        cards = _process_image_sync("uploads/test.jpg", "job-1")

    assert any(c.status == CardStatus.unidentified for c in cards)
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_tasks.py -v
```
Expected: ImportError.

**Step 3: Create backend/app/celery_app.py**

```python
import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "deck_doctor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
)
```

**Step 4: Create backend/app/tasks.py**

```python
import asyncio
import json
import uuid
import cv2
import numpy as np
from pathlib import Path

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import Card, CardStatus
from app.pipeline.detect import detect_cards
from app.pipeline.ocr import extract_title
from app.pipeline.scryfall import lookup_card

def _process_image_sync(image_path: str, job_id: str) -> list[Card]:
    img = cv2.imread(image_path)
    if img is None:
        return []

    regions = detect_cards(img)
    db = SessionLocal()
    created_cards = []

    try:
        for region in regions:
            card_id = str(uuid.uuid4())
            title = extract_title(region.crop)

            if title:
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
            created_cards.append(card)

            # Publish SSE event via Redis
            _publish_event(job_id, card)

    finally:
        db.close()

    return created_cards

def _publish_event(job_id: str, card: Card):
    """Publish a card result event to Redis for SSE streaming."""
    import redis
    import os
    r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    event_data = json.dumps({
        "card_id": card.id,
        "name": card.name,
        "status": card.status.value,
        "image_url": card.image_url,
    })
    r.publish(f"job:{job_id}", event_data)

@celery_app.task(name="process_image")
def process_image(image_path: str, job_id: str):
    return _process_image_sync(image_path, job_id)
```

**Step 5: Run tests**

```bash
cd backend
pytest tests/test_tasks.py -v
```
Expected: 2 passed.

**Step 6: Commit**

```bash
git add backend/app/celery_app.py backend/app/tasks.py backend/tests/test_tasks.py
git commit -m "feat: add Celery task for card processing pipeline"
```

---

## Task 7: FastAPI App & Routes

**Files:**
- Create: `backend/app/main.py`
- Create: `backend/app/routers/__init__.py`
- Create: `backend/app/routers/upload.py`
- Create: `backend/app/routers/cards.py`
- Create: `backend/app/routers/events.py`
- Create: `backend/tests/test_api.py`

**Step 1: Write failing tests**

```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from unittest.mock import patch
from app.main import app
from app.database import Base, get_db
from app.models import Card, CardStatus

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

    with patch("app.routers.cards.lookup_card", return_value=fake_scryfall):
        resp = client.patch("/api/cards/c2/fix", json={"name": "Black Lotus"})

    assert resp.status_code == 200
    assert resp.json()["name"] == "Black Lotus"
    assert resp.json()["status"] == "identified"
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_api.py -v
```
Expected: ImportError.

**Step 3: Create backend/app/routers/upload.py**

```python
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Annotated

router = APIRouter()
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILES = 10

@router.post("/upload")
async def upload_images(files: Annotated[list[UploadFile], File()]):
    if len(files) > MAX_FILES:
        raise HTTPException(400, f"Max {MAX_FILES} files per upload")

    job_id = str(uuid.uuid4())
    paths = []

    for file in files:
        ext = Path(file.filename or "img.jpg").suffix or ".jpg"
        dest = UPLOAD_DIR / f"{uuid.uuid4()}{ext}"
        content = await file.read()
        dest.write_bytes(content)
        paths.append(str(dest))

    # Enqueue Celery tasks
    from app.tasks import process_image
    for path in paths:
        process_image.delay(path, job_id)

    return {"job_id": job_id, "queued": len(paths)}
```

**Step 4: Create backend/app/routers/cards.py**

```python
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
```

**Step 5: Create backend/app/routers/events.py**

```python
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
                    # End stream signal (sent by worker when job is done)
                    if data.get("done"):
                        break
        finally:
            await pubsub.unsubscribe(f"job:{job_id}")
            await r.aclose()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Step 6: Create backend/app/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import upload, cards, events

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Deck Doctor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(cards.router, prefix="/api")
app.include_router(events.router, prefix="/api")
```

**Step 7: Run tests**

```bash
cd backend
pytest tests/test_api.py -v
```
Expected: 4 passed.

**Step 8: Run all backend tests**

```bash
cd backend
pytest -v
```
Expected: All pass.

**Step 9: Commit**

```bash
git add backend/app/ backend/tests/test_api.py
git commit -m "feat: add FastAPI routes for upload, cards, and SSE events"
```

---

## Task 8: Frontend — Types, API Client & Routing

**Files:**
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`
- Modify: `frontend/index.html`

**Step 1: Create frontend/src/types.ts**

```typescript
export type CardStatus = "processing" | "identified" | "unidentified";

export interface Card {
  id: string;
  name: string | null;
  scryfall_id: string | null;
  image_url: string | null;
  colors: string | null;        // JSON string e.g. '["R","G"]'
  color_identity: string | null;
  type_line: string | null;
  mana_cost: string | null;
  oracle_text: string | null;
  status: CardStatus;
  created_at: string;
  source_image: string;
}

export interface UploadResponse {
  job_id: string;
  queued: number;
}

export interface SSECardEvent {
  card_id: string;
  name: string | null;
  status: CardStatus;
  image_url: string | null;
  done?: boolean;
}
```

**Step 2: Create frontend/src/api/client.ts**

```typescript
import type { Card, UploadResponse } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function uploadImages(files: File[]): Promise<UploadResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function fetchCards(): Promise<Card[]> {
  const res = await fetch(`${BASE}/api/cards`);
  if (!res.ok) throw new Error("Failed to fetch cards");
  return res.json();
}

export async function fixCard(cardId: string, name: string): Promise<Card> {
  const res = await fetch(`${BASE}/api/cards/${cardId}/fix`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Fix failed");
  return res.json();
}

export function createSSEConnection(jobId: string): EventSource {
  return new EventSource(`${BASE}/api/events/${jobId}`);
}
```

**Step 3: Create frontend/src/App.tsx**

```tsx
import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import LibraryPage from "./pages/LibraryPage";

type Tab = "upload" | "library";

export default function App() {
  const [tab, setTab] = useState<Tab>("upload");

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-8">
        <span className="font-bold text-xl text-amber-400">Deck Doctor</span>
        <button
          onClick={() => setTab("upload")}
          className={`text-sm font-medium pb-1 border-b-2 transition-colors ${
            tab === "upload"
              ? "border-amber-400 text-amber-400"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          Upload
        </button>
        <button
          onClick={() => setTab("library")}
          className={`text-sm font-medium pb-1 border-b-2 transition-colors ${
            tab === "library"
              ? "border-amber-400 text-amber-400"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          Library
        </button>
      </nav>
      <main className="p-6">
        {tab === "upload" ? (
          <UploadPage onDone={() => setTab("library")} />
        ) : (
          <LibraryPage />
        )}
      </main>
    </div>
  );
}
```

**Step 4: Update frontend/src/main.tsx**

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

**Step 5: Update frontend/tailwind.config.js**

```js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

**Step 6: Update frontend/src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Step 7: Commit**

```bash
git add frontend/src/
git commit -m "feat: add frontend types, API client, and app shell"
```

---

## Task 9: Upload Page Component

**Files:**
- Create: `frontend/src/pages/UploadPage.tsx`
- Create: `frontend/src/components/UploadZone.tsx`
- Create: `frontend/src/components/ProgressFeed.tsx`
- Create: `frontend/src/hooks/useSSE.ts`

**Step 1: Create frontend/src/hooks/useSSE.ts**

```typescript
import { useEffect, useState } from "react";
import { createSSEConnection } from "../api/client";
import type { SSECardEvent } from "../types";

export function useSSE(jobId: string | null) {
  const [events, setEvents] = useState<SSECardEvent[]>([]);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    setEvents([]);
    setDone(false);

    const es = createSSEConnection(jobId);
    es.onmessage = (e) => {
      const data: SSECardEvent = JSON.parse(e.data);
      if (data.done) {
        setDone(true);
        es.close();
      } else {
        setEvents((prev) => [...prev, data]);
      }
    };
    es.onerror = () => { setDone(true); es.close(); };

    return () => es.close();
  }, [jobId]);

  return { events, done };
}
```

**Step 2: Create frontend/src/components/UploadZone.tsx**

```tsx
import { useRef, useState } from "react";

interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

const MAX = 10;
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

export default function UploadZone({ onFiles, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handle(files: FileList | null) {
    if (!files) return;
    const valid = Array.from(files)
      .filter((f) => ACCEPTED.includes(f.type))
      .slice(0, MAX);
    if (valid.length) onFiles(valid);
  }

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files); }}
      className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-colors ${
        dragging
          ? "border-amber-400 bg-amber-400/10"
          : disabled
          ? "border-gray-700 opacity-50 cursor-not-allowed"
          : "border-gray-700 hover:border-gray-500"
      }`}
    >
      <p className="text-lg font-medium text-gray-300">
        Drop card photos here or click to browse
      </p>
      <p className="text-sm text-gray-500 mt-1">
        Up to {MAX} images • JPG, PNG, WebP
      </p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        multiple
        className="hidden"
        onChange={(e) => handle(e.target.files)}
        disabled={disabled}
      />
    </div>
  );
}
```

**Step 3: Create frontend/src/components/ProgressFeed.tsx**

```tsx
import type { SSECardEvent } from "../types";

interface Props {
  events: SSECardEvent[];
  done: boolean;
}

export default function ProgressFeed({ events, done }: Props) {
  if (!events.length && !done) return null;

  return (
    <div className="mt-6 space-y-2">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
        Processing
      </h3>
      <ul className="space-y-1">
        {events.map((e, i) => (
          <li key={i} className="flex items-center gap-2 text-sm">
            {e.status === "identified" ? (
              <span className="text-green-400">✓</span>
            ) : (
              <span className="text-red-400">✗</span>
            )}
            <span className={e.status === "identified" ? "text-gray-200" : "text-gray-500"}>
              {e.name ?? "Unidentified card"}
            </span>
          </li>
        ))}
      </ul>
      {done && (
        <p className="text-sm text-amber-400 mt-3">
          Done — {events.filter((e) => e.status === "identified").length} of{" "}
          {events.length} identified
        </p>
      )}
    </div>
  );
}
```

**Step 4: Create frontend/src/pages/UploadPage.tsx**

```tsx
import { useState } from "react";
import UploadZone from "../components/UploadZone";
import ProgressFeed from "../components/ProgressFeed";
import { uploadImages } from "../api/client";
import { useSSE } from "../hooks/useSSE";

interface Props {
  onDone: () => void;
}

export default function UploadPage({ onDone }: Props) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { events, done } = useSSE(jobId);

  async function handleFiles(files: File[]) {
    setError(null);
    setUploading(true);
    try {
      const resp = await uploadImages(files);
      setJobId(resp.job_id);
    } catch {
      setError("Upload failed. Is the backend running?");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Upload Cards</h1>
      <UploadZone onFiles={handleFiles} disabled={uploading || !!jobId} />
      {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
      <ProgressFeed events={events} done={done} />
      {done && (
        <button
          onClick={onDone}
          className="mt-6 px-6 py-2 bg-amber-500 hover:bg-amber-400 text-black font-semibold rounded-lg transition-colors"
        >
          View Library →
        </button>
      )}
    </div>
  );
}
```

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add upload page with drag-and-drop and SSE progress feed"
```

---

## Task 10: Library Page — Hooks, Search, Filters

**Files:**
- Create: `frontend/src/hooks/useLibrary.ts`
- Create: `frontend/src/components/SearchBar.tsx`
- Create: `frontend/src/components/ColorFilter.tsx`
- Create: `frontend/src/components/TypeFilter.tsx`

**Step 1: Create frontend/src/hooks/useLibrary.ts**

```typescript
import { useEffect, useMemo, useState } from "react";
import Fuse from "fuse.js";
import { fetchCards } from "../api/client";
import type { Card } from "../types";

const COLOR_LABELS: Record<string, string> = {
  W: "White", U: "Blue", B: "Black", R: "Red", G: "Green",
};

const TYPE_KEYWORDS = [
  "Creature", "Instant", "Sorcery", "Enchantment",
  "Artifact", "Planeswalker", "Land",
];

export function useLibrary() {
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [colorFilter, setColorFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  useEffect(() => {
    fetchCards()
      .then(setCards)
      .finally(() => setLoading(false));
  }, []);

  const fuse = useMemo(
    () => new Fuse(cards, { keys: ["name"], threshold: 0.4 }),
    [cards]
  );

  const filtered = useMemo(() => {
    let result = search
      ? fuse.search(search).map((r) => r.item)
      : cards;

    if (colorFilter) {
      if (colorFilter === "Colorless") {
        result = result.filter((c) => {
          const colors = c.colors ? JSON.parse(c.colors) : [];
          return colors.length === 0;
        });
      } else if (colorFilter === "Multicolor") {
        result = result.filter((c) => {
          const colors = c.colors ? JSON.parse(c.colors) : [];
          return colors.length > 1;
        });
      } else {
        result = result.filter((c) => {
          const colors = c.colors ? JSON.parse(c.colors) : [];
          return colors.includes(colorFilter) && colors.length === 1;
        });
      }
    }

    if (typeFilter) {
      result = result.filter((c) =>
        c.type_line?.includes(typeFilter) ?? false
      );
    }

    return result;
  }, [cards, search, colorFilter, typeFilter, fuse]);

  return {
    cards: filtered,
    loading,
    search, setSearch,
    colorFilter, setColorFilter,
    typeFilter, setTypeFilter,
    COLOR_LABELS,
    TYPE_KEYWORDS,
  };
}
```

**Step 2: Create frontend/src/components/SearchBar.tsx**

```tsx
interface Props {
  value: string;
  onChange: (v: string) => void;
}

export default function SearchBar({ value, onChange }: Props) {
  return (
    <input
      type="search"
      placeholder="Search cards..."
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-amber-500"
    />
  );
}
```

**Step 3: Create frontend/src/components/ColorFilter.tsx**

```tsx
const COLORS = [
  { key: "W", label: "White", bg: "bg-yellow-50 text-gray-900" },
  { key: "U", label: "Blue", bg: "bg-blue-600 text-white" },
  { key: "B", label: "Black", bg: "bg-gray-900 text-white border border-gray-600" },
  { key: "R", label: "Red", bg: "bg-red-600 text-white" },
  { key: "G", label: "Green", bg: "bg-green-700 text-white" },
  { key: "Colorless", label: "Colorless", bg: "bg-gray-500 text-white" },
  { key: "Multicolor", label: "Multi", bg: "bg-gradient-to-r from-yellow-400 to-blue-500 text-white" },
];

interface Props {
  value: string | null;
  onChange: (v: string | null) => void;
}

export default function ColorFilter({ value, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {COLORS.map((c) => (
        <button
          key={c.key}
          onClick={() => onChange(value === c.key ? null : c.key)}
          className={`px-3 py-1 rounded-full text-xs font-semibold transition-opacity ${c.bg} ${
            value && value !== c.key ? "opacity-40" : "opacity-100"
          }`}
        >
          {c.label}
        </button>
      ))}
    </div>
  );
}
```

**Step 4: Create frontend/src/components/TypeFilter.tsx**

```tsx
const TYPES = ["Creature", "Instant", "Sorcery", "Enchantment", "Artifact", "Planeswalker", "Land"];

interface Props {
  value: string | null;
  onChange: (v: string | null) => void;
}

export default function TypeFilter({ value, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {TYPES.map((t) => (
        <button
          key={t}
          onClick={() => onChange(value === t ? null : t)}
          className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
            value === t
              ? "bg-amber-500 border-amber-500 text-black"
              : "border-gray-700 text-gray-400 hover:border-gray-500"
          }`}
        >
          {t}
        </button>
      ))}
    </div>
  );
}
```

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: add library hooks and search/filter components"
```

---

## Task 11: Library Page — Card Views

**Files:**
- Create: `frontend/src/components/CardTile.tsx`
- Create: `frontend/src/components/LibraryTileView.tsx`
- Create: `frontend/src/components/LibraryGridView.tsx`
- Create: `frontend/src/components/FixCardModal.tsx`
- Create: `frontend/src/pages/LibraryPage.tsx`

**Step 1: Create frontend/src/components/CardTile.tsx**

```tsx
import type { Card } from "../types";

const PLACEHOLDER = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='280' viewBox='0 0 200 280'%3E%3Crect width='200' height='280' fill='%23374151'/%3E%3Ctext x='100' y='145' text-anchor='middle' fill='%236B7280' font-size='14'%3E%3F%3C/text%3E%3C/svg%3E";

interface Props {
  card: Card;
  onFix?: (card: Card) => void;
}

export default function CardTile({ card, onFix }: Props) {
  return (
    <div className="group relative rounded-lg overflow-hidden bg-gray-900 border border-gray-800 hover:border-amber-500/50 transition-colors">
      <img
        src={card.image_url ?? PLACEHOLDER}
        alt={card.name ?? "Unidentified card"}
        className="w-full object-cover"
        loading="lazy"
      />
      {card.status === "unidentified" && onFix && (
        <div className="absolute inset-0 bg-black/70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => onFix(card)}
            className="px-4 py-2 bg-amber-500 text-black font-semibold rounded-lg text-sm"
          >
            Fix Card
          </button>
        </div>
      )}
      <div className="p-2">
        <p className="text-xs text-gray-400 truncate">
          {card.name ?? <span className="text-red-400">Unidentified</span>}
        </p>
        {card.type_line && (
          <p className="text-xs text-gray-600 truncate">{card.type_line}</p>
        )}
      </div>
    </div>
  );
}
```

**Step 2: Create frontend/src/components/LibraryTileView.tsx**

```tsx
import type { Card } from "../types";
import CardTile from "./CardTile";

interface Props {
  cards: Card[];
  onFix: (card: Card) => void;
}

export default function LibraryTileView({ cards, onFix }: Props) {
  if (!cards.length) {
    return <p className="text-gray-500 text-sm py-8 text-center">No cards found.</p>;
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
      {cards.map((card) => (
        <CardTile key={card.id} card={card} onFix={onFix} />
      ))}
    </div>
  );
}
```

**Step 3: Create frontend/src/components/LibraryGridView.tsx**

```tsx
import type { Card } from "../types";

interface Props {
  cards: Card[];
  onFix: (card: Card) => void;
}

function parseColors(colorsJson: string | null): string {
  if (!colorsJson) return "—";
  try {
    const arr: string[] = JSON.parse(colorsJson);
    return arr.length ? arr.join(", ") : "Colorless";
  } catch {
    return "—";
  }
}

export default function LibraryGridView({ cards, onFix }: Props) {
  if (!cards.length) {
    return <p className="text-gray-500 text-sm py-8 text-center">No cards found.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-gray-800 text-gray-500 uppercase text-xs">
            <th className="py-2 pr-4">Name</th>
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">Color</th>
            <th className="py-2 pr-4">Mana Cost</th>
            <th className="py-2"></th>
          </tr>
        </thead>
        <tbody>
          {cards.map((card) => (
            <tr key={card.id} className="border-b border-gray-900 hover:bg-gray-900/50">
              <td className="py-2 pr-4 font-medium text-gray-200">
                {card.name ?? <span className="text-red-400">Unidentified</span>}
              </td>
              <td className="py-2 pr-4 text-gray-400">{card.type_line ?? "—"}</td>
              <td className="py-2 pr-4 text-gray-400">{parseColors(card.colors)}</td>
              <td className="py-2 pr-4 text-gray-400 font-mono">{card.mana_cost ?? "—"}</td>
              <td className="py-2">
                {card.status === "unidentified" && (
                  <button
                    onClick={() => onFix(card)}
                    className="text-xs text-amber-400 hover:text-amber-300"
                  >
                    Fix
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**Step 4: Create frontend/src/components/FixCardModal.tsx**

```tsx
import { useState } from "react";
import type { Card } from "../types";
import { fixCard } from "../api/client";

interface Props {
  card: Card;
  onClose: () => void;
  onFixed: (updated: Card) => void;
}

export default function FixCardModal({ card, onClose, onFixed }: Props) {
  const [name, setName] = useState(card.name ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await fixCard(card.id, name.trim());
      onFixed(updated);
    } catch {
      setError("Card not found on Scryfall. Check the name and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-sm">
        <h2 className="text-lg font-bold mb-4">Fix Card Name</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            autoFocus
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Card name..."
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
          />
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-3 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-amber-500 text-black font-semibold rounded-lg text-sm disabled:opacity-50"
            >
              {loading ? "Looking up..." : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
```

**Step 5: Create frontend/src/pages/LibraryPage.tsx**

```tsx
import { useState } from "react";
import { useLibrary } from "../hooks/useLibrary";
import SearchBar from "../components/SearchBar";
import ColorFilter from "../components/ColorFilter";
import TypeFilter from "../components/TypeFilter";
import LibraryTileView from "../components/LibraryTileView";
import LibraryGridView from "../components/LibraryGridView";
import FixCardModal from "../components/FixCardModal";
import type { Card } from "../types";

type View = "tile" | "grid";

export default function LibraryPage() {
  const {
    cards, loading,
    search, setSearch,
    colorFilter, setColorFilter,
    typeFilter, setTypeFilter,
  } = useLibrary();

  const [view, setView] = useState<View>("tile");
  const [fixingCard, setFixingCard] = useState<Card | null>(null);
  const [cardMap, setCardMap] = useState<Record<string, Card>>({});

  // Merge fixed cards back into display list
  const displayCards = cards.map((c) => cardMap[c.id] ?? c);

  function handleFixed(updated: Card) {
    setCardMap((prev) => ({ ...prev, [updated.id]: updated }));
    setFixingCard(null);
  }

  if (loading) {
    return <p className="text-gray-500 text-sm">Loading library...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Library <span className="text-gray-500 text-lg font-normal">({cards.length})</span></h1>
        <div className="flex gap-2">
          <button
            onClick={() => setView("tile")}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              view === "tile" ? "bg-amber-500 text-black" : "bg-gray-800 text-gray-400"
            }`}
          >
            Tiles
          </button>
          <button
            onClick={() => setView("grid")}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              view === "grid" ? "bg-amber-500 text-black" : "bg-gray-800 text-gray-400"
            }`}
          >
            Grid
          </button>
        </div>
      </div>

      <SearchBar value={search} onChange={setSearch} />

      <div className="space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wide">Color</p>
        <ColorFilter value={colorFilter} onChange={setColorFilter} />
      </div>

      <div className="space-y-2">
        <p className="text-xs text-gray-500 uppercase tracking-wide">Type</p>
        <TypeFilter value={typeFilter} onChange={setTypeFilter} />
      </div>

      {view === "tile" ? (
        <LibraryTileView cards={displayCards} onFix={setFixingCard} />
      ) : (
        <LibraryGridView cards={displayCards} onFix={setFixingCard} />
      )}

      {fixingCard && (
        <FixCardModal
          card={fixingCard}
          onClose={() => setFixingCard(null)}
          onFixed={handleFixed}
        />
      )}
    </div>
  );
}
```

**Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: add library page with tile/grid views and fix modal"
```

---

## Task 12: Frontend Dockerfile & Final Wiring

**Files:**
- Create: `frontend/Dockerfile`
- Modify: `frontend/vite.config.ts`

**Step 1: Create frontend/Dockerfile**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
```

**Step 2: Update frontend/vite.config.ts**

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": "http://backend:8000",
    },
  },
});
```

**Step 3: Smoke test — start Docker Compose**

```bash
docker compose up --build
```

Expected:
- `http://localhost:5173` — React app loads
- `http://localhost:8000/docs` — FastAPI Swagger UI loads
- Redis running on 6379
- Celery worker connected

**Step 4: Run all backend tests one final time**

```bash
docker compose exec backend pytest -v
```
Expected: All pass.

**Step 5: Final commit**

```bash
git add frontend/Dockerfile frontend/vite.config.ts
git commit -m "feat: add frontend Dockerfile and finalize Docker Compose wiring"
```

---

## Done

The app is fully implemented. To run locally without Docker:

```bash
# Terminal 1 — Redis
docker run -p 6379:6379 redis:7-alpine

# Terminal 2 — Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 3 — Celery worker
cd backend && celery -A app.celery_app worker --loglevel=info

# Terminal 4 — Frontend
cd frontend && npm install && npm run dev
```
