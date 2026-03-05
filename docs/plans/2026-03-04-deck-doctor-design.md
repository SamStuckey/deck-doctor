# Deck Doctor — Design Document
**Date:** 2026-03-04

## Overview

A web app for scanning and cataloguing Magic: The Gathering cards. Users photograph spreads of cards (one or many per photo), the app detects each card, reads its title via OCR, looks it up on Scryfall, and stores the result in a persistent library.

---

## Architecture

```
┌─────────────────────────────────┐
│         React (Vite)            │  ← Upload, Library, Search/Filter
└────────────────┬────────────────┘
                 │ REST + SSE (progress)
┌────────────────▼────────────────┐
│         FastAPI (Python)        │  ← REST API, SSE endpoint
└──────┬──────────────────┬───────┘
       │                  │
┌──────▼──────┐   ┌───────▼──────┐
│   SQLite    │   │  Celery +    │  ← Async card processing
│  (cards DB) │   │  Redis       │
└─────────────┘   └───────┬──────┘
                          │
              ┌───────────▼───────────┐
              │   Processing Pipeline │
              │  1. YOLOv8 detect     │
              │  2. Crop each card    │
              │  3. PaddleOCR title   │
              │  4. Scryfall lookup   │
              │  5. Save to DB        │
              └───────────────────────┘
```

---

## Processing Pipeline

1. **Upload** — User uploads 1–10 photos (drag-and-drop). `POST /api/upload` saves files to disk and enqueues one Celery task per image.
2. **Card Detection** — YOLOv8 (Ultralytics) detects card bounding boxes in the photo. Falls back to OpenCV contour detection if needed. Each detected card region is cropped.
3. **OCR** — PaddleOCR runs on the top-left ~20% of each cropped card (title region). The extracted string is cleaned.
4. **Scryfall Lookup** — Calls `GET /cards/named?fuzzy=<name>`. Returns canonical name, colors, type_line, mana_cost, image_uris.normal, oracle_text. If no match, card saved as `unidentified`.
5. **Progress** — Frontend subscribes to a Server-Sent Events (SSE) stream scoped to the upload job. Each card completion streams a status update for live UI feedback.

---

## Data Model

```
Card
  id             UUID (primary key)
  name           TEXT (nullable — null if unidentified)
  scryfall_id    TEXT (nullable)
  image_url      TEXT (Scryfall normal image URL, nullable)
  colors         TEXT (JSON array: ["W","U","B","R","G"])
  color_identity TEXT (JSON array)
  type_line      TEXT
  mana_cost      TEXT
  oracle_text    TEXT
  status         ENUM: processing | identified | unidentified
  created_at     DATETIME
  source_image   TEXT (path to original uploaded photo)
```

Unidentified cards have `name = null` and `image_url = null`. The UI shows a placeholder image and a "Fix" button allowing the user to manually enter the correct name, which re-triggers the Scryfall lookup.

---

## Frontend

### Upload Page
- Drag-and-drop zone, max 10 images
- Real-time progress feed via SSE: "Found: Lightning Bolt ✓" / "Unidentified ✗"
- After processing, link to Library

### Library Page
- **Tile view** — responsive card image grid (Scryfall art)
- **Grid view** — compact data table (name, colors, type, mana cost)
- Toggle between views
- **Fuzzy search** — client-side instant search by card name
- **Color filters** — W / U / B / R / G / Colorless / Multicolor
- **Type filters** — Creature / Instant / Sorcery / Enchantment / Artifact / Planeswalker / Land

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Backend | FastAPI + Python 3.11 | Async-native, fast, ideal for ML pipelines |
| Frontend | React + Vite + TypeScript | Modern, fast DX |
| Styling | Tailwind CSS | Utility-first, no component library overhead |
| Database | SQLite + SQLAlchemy | Zero-config, easy to migrate to Postgres later |
| Task Queue | Celery + Redis | Async processing, live progress streaming |
| Card Detection | YOLOv8 (Ultralytics) | Pre-trained, free, handles overlapping cards |
| OCR | PaddleOCR | Best free accuracy on stylized/non-standard fonts |
| Card API | Scryfall | Free, comprehensive, no auth required |

---

## Deployment

Web-deployable. Intended as a hosted service accessible to multiple users. No user auth in v1 — shared library. Docker Compose for local dev (FastAPI + Redis + Celery worker). Can be containerized for deployment.

---

## Out of Scope (v1)

- User accounts / per-user libraries
- Deck building / deck management
- Card pricing / market data
- Multiple printing selection (uses Scryfall's default/canonical printing)
- Duplicate detection
