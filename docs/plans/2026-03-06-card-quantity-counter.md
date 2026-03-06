# Card Quantity Counter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Collapse duplicate cards in the library into a single tile with a quantity stepper (− N +), where − removes one DB row and + duplicates one row.

**Architecture:** All grouping is client-side in `useLibrary`. The DB keeps one row per physical card. A new `POST /api/cards/{id}/copy` endpoint duplicates a row. `LibraryTileView` and `CardTile` receive `CardGroup` objects instead of raw `Card` objects. `LibraryPage` manages optimistic state for counts.

**Tech Stack:** FastAPI (Python 3.11), SQLAlchemy, React 18, TypeScript, Tailwind CSS

---

### Task 1: Backend — `POST /api/cards/{card_id}/copy` endpoint

**Files:**
- Modify: `backend/app/routers/cards.py`
- Test: `backend/tests/test_cards.py`

**Context:**
- `Card` model is in `backend/app/models.py`. All fields are plain columns — no relationships.
- `CardOut` schema is in `backend/app/schemas.py`.
- Existing routes: `GET /api/cards`, `DELETE /api/cards/{id}`, `PATCH /api/cards/{id}/fix`.
- Run tests inside Docker only: `docker compose run --rm --no-deps backend python -m pytest tests/test_cards.py -v`

**Step 1: Write the failing test**

Open `backend/tests/test_cards.py` and add:

```python
def test_copy_card_returns_201_with_new_id(client, db_session):
    from app.models import Card, CardStatus
    import uuid
    original = Card(
        id=str(uuid.uuid4()),
        name="Lightning Bolt",
        scryfall_id="abc",
        image_url="http://example.com/img.jpg",
        colors='["R"]',
        color_identity='["R"]',
        type_line="Instant",
        mana_cost="{R}",
        oracle_text="Deal 3 damage.",
        status=CardStatus.identified,
        source_image="upload/test.jpg",
    )
    db_session.add(original)
    db_session.commit()

    response = client.post(f"/api/cards/{original.id}/copy")
    assert response.status_code == 201
    data = response.json()
    assert data["id"] != original.id
    assert data["name"] == "Lightning Bolt"
    assert data["scryfall_id"] == "abc"
    assert data["source_image"] == "upload/test.jpg"


def test_copy_card_404_for_missing(client):
    response = client.post("/api/cards/nonexistent-id/copy")
    assert response.status_code == 404
```

**Step 2: Run to confirm FAIL**

```bash
docker compose run --rm --no-deps backend python -m pytest tests/test_cards.py::test_copy_card_returns_201_with_new_id tests/test_cards.py::test_copy_card_404_for_missing -v
```

Expected: FAIL with `405 Method Not Allowed` or `404`.

**Step 3: Implement the endpoint**

In `backend/app/routers/cards.py`, add after the existing `delete_card` route:

```python
@router.post("/cards/{card_id}/copy", response_model=CardOut, status_code=201)
def copy_card(card_id: str, db: Session = Depends(get_db)):
    original = db.get(Card, card_id)
    if not original:
        raise HTTPException(404, "Card not found")
    copy = Card(
        name=original.name,
        scryfall_id=original.scryfall_id,
        image_url=original.image_url,
        colors=original.colors,
        color_identity=original.color_identity,
        type_line=original.type_line,
        mana_cost=original.mana_cost,
        oracle_text=original.oracle_text,
        status=original.status,
        source_image=original.source_image,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy
```

Note: `id` and `created_at` are omitted so their defaults (new UUID, `datetime.utcnow`) apply.

**Step 4: Run to confirm PASS**

```bash
docker compose run --rm --no-deps backend python -m pytest tests/test_cards.py::test_copy_card_returns_201_with_new_id tests/test_cards.py::test_copy_card_404_for_missing -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/app/routers/cards.py backend/tests/test_cards.py
git commit -m "feat: add POST /api/cards/{id}/copy endpoint"
```

---

### Task 2: Frontend — `copyCard` API client function + `CardGroup` type

**Files:**
- Modify: `frontend/src/api/client.ts`
- Modify: `frontend/src/types.ts`

**Context:**
- `client.ts` uses `BASE = import.meta.env.VITE_API_URL ?? ""` for all REST calls.
- `types.ts` currently exports `Card`, `UploadResponse`, `SSECardEvent`.
- No test framework for frontend — verify by TypeScript compilation: `cd frontend && npx tsc --noEmit`.

**Step 1: Add `CardGroup` type to `types.ts`**

Append to `frontend/src/types.ts`:

```typescript
export interface CardGroup {
  card: Card;       // representative card for display
  count: number;    // total copies in DB
  ids: string[];    // all DB row IDs for this group (oldest first)
}
```

**Step 2: Add `copyCard` to `client.ts`**

Append to `frontend/src/api/client.ts`:

```typescript
export async function copyCard(cardId: string): Promise<Card> {
  const res = await fetch(`${BASE}/api/cards/${cardId}`, { method: "POST" });
  // Note: the copy endpoint is /api/cards/{id}/copy
  const res2 = await fetch(`${BASE}/api/cards/${cardId}/copy`, { method: "POST" });
  if (!res2.ok) throw new Error(`Copy failed (${res2.status})`);
  return res2.json();
}
```

Wait — write it correctly (no duplicate fetch):

```typescript
export async function copyCard(cardId: string): Promise<Card> {
  const res = await fetch(`${BASE}/api/cards/${cardId}/copy`, { method: "POST" });
  if (!res.ok) throw new Error(`Copy failed (${res.status})`);
  return res.json();
}
```

**Step 3: Verify TypeScript compiles**

```bash
cd /Users/samuelstuckey/deck_doctor/frontend && npx tsc --noEmit
```

Expected: no errors.

**Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/client.ts
git commit -m "feat: add CardGroup type and copyCard API function"
```

---

### Task 3: Frontend — grouping logic in `useLibrary`

**Files:**
- Modify: `frontend/src/hooks/useLibrary.ts`

**Context:**
- `useLibrary` currently returns `cards: Card[]` (filtered/searched).
- Grouping key: for identified cards use `scryfall_id`; for unidentified cards (where `scryfall_id` is null) use `name ?? id` so each distinct unidentified card is its own group.
- The `total` returned is currently `allCards.length` — keep it as total unique groups.
- `fuse` searches on the pre-grouped cards array (search on representative cards is correct).
- No test framework for frontend — verify with `npx tsc --noEmit`.

**Step 1: Add `groupCards` helper**

In `useLibrary.ts`, add this pure function before `useLibrary`:

```typescript
function groupCards(cards: Card[]): CardGroup[] {
  const map = new Map<string, CardGroup>();
  for (const card of cards) {
    const key = card.scryfall_id ?? card.name ?? card.id;
    const existing = map.get(key);
    if (existing) {
      existing.count += 1;
      existing.ids.push(card.id);
    } else {
      map.set(key, { card, count: 1, ids: [card.id] });
    }
  }
  return Array.from(map.values());
}
```

Also add the import at the top of the file:
```typescript
import type { Card, CardGroup } from "../types";
```

**Step 2: Change `useLibrary` return value**

Replace the `cards` memo and `total` in the return:

```typescript
const groups = useMemo(() => groupCards(cards), [cards]);

return {
  groups,                          // CardGroup[] — replaces cards
  total: groups.length,            // unique cards, not raw rows
  loading,
  search, setSearch,
  colorFilter, setColorFilter,
  typeFilter, setTypeFilter,
};
```

The existing `cards` memo (filtered/searched `Card[]`) still exists internally — it feeds `groupCards`. Only the public API changes from `cards: Card[]` to `groups: CardGroup[]`.

**Step 3: Verify TypeScript compiles**

```bash
cd /Users/samuelstuckey/deck_doctor/frontend && npx tsc --noEmit
```

Expected: errors on callers of `useLibrary` (they still reference `.cards`). That's expected — they'll be fixed in Task 4.

**Step 4: Commit**

```bash
git add frontend/src/hooks/useLibrary.ts
git commit -m "feat: group cards by scryfall_id in useLibrary"
```

---

### Task 4: Frontend — update `LibraryPage` for groups + optimistic state

**Files:**
- Modify: `frontend/src/pages/LibraryPage.tsx`

**Context:**
- `LibraryPage` currently uses `cards` from `useLibrary` and passes individual `Card` objects to views.
- It manages `overrides: Record<string, Card>` (for Fix Card flow) and `deletedIds: Set<string>`.
- New state needed: `countOverrides: Record<string, { count: number; ids: string[] }>` — keyed by the group representative card's ID, stores optimistic count adjustments.
- When `−` is pressed: call `deleteCard(ids[ids.length - 1])` (remove the last-added copy), then remove that ID from local state.
- When `+` is pressed: call `copyCard(ids[0])` (copy the representative), then add the new card's ID to local state.
- `displayCards` (the current filtered+overridden array) becomes `displayGroups`.
- Pass `onIncrement` and `onDecrement` down to tile view instead of `onDelete`.

**Step 1: Rewrite `LibraryPage.tsx`**

Replace the entire file with:

```tsx
import { useState } from "react";
import { useLibrary } from "../hooks/useLibrary";
import SearchBar from "../components/SearchBar";
import ColorFilter from "../components/ColorFilter";
import TypeFilter from "../components/TypeFilter";
import LibraryTileView from "../components/LibraryTileView";
import LibraryGridView from "../components/LibraryGridView";
import FixCardModal from "../components/FixCardModal";
import { deleteCard, copyCard } from "../api/client";
import type { Card, CardGroup } from "../types";

type View = "tile" | "grid";

export default function LibraryPage() {
  const {
    groups, total, loading,
    search, setSearch,
    colorFilter, setColorFilter,
    typeFilter, setTypeFilter,
  } = useLibrary();

  const [view, setView] = useState<View>("tile");
  const [fixingCard, setFixingCard] = useState<Card | null>(null);
  const [overrides, setOverrides] = useState<Record<string, Card>>({});
  // countOverrides: keyed by representative card id → { delta, extraIds }
  const [countDeltas, setCountDeltas] = useState<Record<string, number>>({});
  const [extraIds, setExtraIds] = useState<Record<string, string[]>>({});
  const [removedIds, setRemovedIds] = useState<Set<string>>(new Set());

  const displayGroups: CardGroup[] = groups
    .map((g) => {
      const repCard = overrides[g.card.id] ?? g.card;
      const activeIds = g.ids.filter((id) => !removedIds.has(id));
      const added = extraIds[g.card.id] ?? [];
      const allIds = [...activeIds, ...added];
      return { card: repCard, count: allIds.length, ids: allIds };
    })
    .filter((g) => g.count > 0);

  function handleFixed(updated: Card) {
    setOverrides((prev) => ({ ...prev, [updated.id]: updated }));
    setFixingCard(null);
  }

  async function handleDecrement(group: CardGroup) {
    const targetId = group.ids[group.ids.length - 1];
    try {
      await deleteCard(targetId);
      setRemovedIds((prev) => new Set(prev).add(targetId));
      setExtraIds((prev) => {
        const extra = (prev[group.card.id] ?? []).filter((id) => id !== targetId);
        return { ...prev, [group.card.id]: extra };
      });
    } catch {
      // silently ignore — count stays if delete fails
    }
  }

  async function handleIncrement(group: CardGroup) {
    try {
      const newCard = await copyCard(group.ids[0]);
      setExtraIds((prev) => ({
        ...prev,
        [group.card.id]: [...(prev[group.card.id] ?? []), newCard.id],
      }));
    } catch {
      // silently ignore — count stays if copy fails
    }
  }

  if (loading) {
    return <p className="text-gray-500 text-sm">Loading library...</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">
          Library{" "}
          <span className="text-gray-500 text-lg font-normal">({total})</span>
        </h1>
        <div className="flex gap-2">
          <button
            onClick={() => setView("tile")}
            aria-pressed={view === "tile"}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              view === "tile" ? "bg-amber-500 text-black" : "bg-gray-800 text-gray-400"
            }`}
          >
            Tiles
          </button>
          <button
            onClick={() => setView("grid")}
            aria-pressed={view === "grid"}
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
        <LibraryTileView
          groups={displayGroups}
          onFix={setFixingCard}
          onDecrement={handleDecrement}
          onIncrement={handleIncrement}
        />
      ) : (
        <LibraryGridView cards={displayGroups.map((g) => g.card)} onFix={setFixingCard} />
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

**Step 2: Verify TypeScript compiles**

```bash
cd /Users/samuelstuckey/deck_doctor/frontend && npx tsc --noEmit
```

Expected: errors on `LibraryTileView` props (it still expects `Card[]` + `onDelete`). That's expected — fixed in Task 5.

**Step 3: Commit**

```bash
git add frontend/src/pages/LibraryPage.tsx
git commit -m "feat: update LibraryPage for CardGroup state and increment/decrement handlers"
```

---

### Task 5: Frontend — update `LibraryTileView` and `CardTile` for quantity stepper

**Files:**
- Modify: `frontend/src/components/LibraryTileView.tsx`
- Modify: `frontend/src/components/CardTile.tsx`

**Context:**
- `LibraryTileView` currently takes `cards: Card[]`, `onFix`, `onDelete`. Replace with `groups: CardGroup[]`, `onFix`, `onDecrement`, `onIncrement`.
- `CardTile` currently takes `card: Card`, `onFix?`, `onDelete?`, `eager?`. Replace `onDelete` with `count: number`, `onDecrement`, `onIncrement`.
- The stepper UI: a badge at the bottom-right of the card image area. At rest: a small pill showing the count (only visible when count > 1, or always visible — see below). On `group-hover`: expands to show `−  N  +`.
- Always show the stepper (even for count=1) so users can always increment or decrement.
- Stepper styling: dark semi-transparent pill, amber text for numbers, gray `−`/`+` buttons that brighten on hover.

**Step 1: Rewrite `LibraryTileView.tsx`**

```tsx
import type { CardGroup } from "../types";
import type { Card } from "../types";
import CardTile from "./CardTile";

interface Props {
  groups: CardGroup[];
  onFix: (card: Card) => void;
  onDecrement: (group: CardGroup) => void;
  onIncrement: (group: CardGroup) => void;
}

export default function LibraryTileView({ groups, onFix, onDecrement, onIncrement }: Props) {
  if (!groups.length) {
    return <p className="text-gray-500 text-sm py-8 text-center">No cards found.</p>;
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
      {groups.map((group, index) => (
        <CardTile
          key={group.card.id}
          card={group.card}
          count={group.count}
          onFix={onFix}
          onDecrement={() => onDecrement(group)}
          onIncrement={() => onIncrement(group)}
          eager={index < 8}
        />
      ))}
    </div>
  );
}
```

**Step 2: Rewrite `CardTile.tsx`**

```tsx
import type { Card } from "../types";

const PLACEHOLDER =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='280' viewBox='0 0 200 280'%3E%3Crect width='200' height='280' fill='%23374151'/%3E%3Ctext x='100' y='145' text-anchor='middle' fill='%236B7280' font-size='14' font-family='sans-serif'%3E%3F%3C/text%3E%3C/svg%3E";

interface Props {
  card: Card;
  count: number;
  onFix?: (card: Card) => void;
  onDecrement?: () => void;
  onIncrement?: () => void;
  eager?: boolean;
}

export default function CardTile({ card, count, onFix, onDecrement, onIncrement, eager }: Props) {
  return (
    <div className="group relative rounded-lg overflow-hidden bg-gray-900 border border-gray-800 hover:border-amber-500/50 transition-all duration-150 cursor-pointer">
      <img
        src={card.image_url ?? PLACEHOLDER}
        alt={card.name ?? "Unidentified card"}
        className="w-full object-cover"
        loading={eager ? "eager" : "lazy"}
      />

      {/* Quantity stepper — shown at rest as count badge, expands to − N + on hover */}
      <div className="absolute bottom-8 right-1.5 flex items-center">
        {/* Rest state: count pill (hidden on hover) */}
        <span className="group-hover:hidden bg-black/70 text-amber-400 text-xs font-bold px-1.5 py-0.5 rounded-full leading-none">
          {count}
        </span>
        {/* Hover state: stepper (hidden at rest) */}
        <div className="hidden group-hover:flex items-center gap-0.5 bg-black/80 rounded-full px-1 py-0.5">
          <button
            onClick={(e) => { e.stopPropagation(); onDecrement?.(); }}
            aria-label="Remove one copy"
            className="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-red-400 transition-colors text-sm font-bold leading-none"
          >
            −
          </button>
          <span className="text-amber-400 text-xs font-bold w-4 text-center">{count}</span>
          <button
            onClick={(e) => { e.stopPropagation(); onIncrement?.(); }}
            aria-label="Add one copy"
            className="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-green-400 transition-colors text-sm font-bold leading-none"
          >
            +
          </button>
        </div>
      </div>

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

**Step 3: Verify TypeScript compiles clean**

```bash
cd /Users/samuelstuckey/deck_doctor/frontend && npx tsc --noEmit
```

Expected: no errors.

**Step 4: Commit**

```bash
git add frontend/src/components/LibraryTileView.tsx frontend/src/components/CardTile.tsx
git commit -m "feat: replace delete button with quantity stepper on card tile"
```

---

### Task 6: Smoke test end-to-end

**Context:**
- The full stack runs via Docker Compose: `docker compose up --build`
- Frontend at `http://localhost:5173`, backend at `http://localhost:8000`

**Step 1: Build and start**

```bash
docker compose up --build
```

Watch for errors in all 4 services (redis, backend, worker, frontend).

**Step 2: Verify grouping**

1. Go to `http://localhost:5173`
2. Upload 2+ images of the same card
3. Navigate to Library
4. Confirm only one tile appears with count badge showing the number of copies

**Step 3: Verify decrement**

1. Hover over the grouped tile — stepper should appear: `− N +`
2. Click `−` until count = 0 — tile should disappear

**Step 4: Verify increment**

1. Hover over any card tile
2. Click `+` — count should increment by 1

**Step 5: Commit if any fixes were needed, then done**

```bash
git add -p
git commit -m "fix: smoke test corrections"
```
