# Card Quantity Counter Design

**Date:** 2026-03-06

**Goal:** Replace the per-card delete button with a quantity stepper (+ / −). Duplicate cards collapse into one tile in the library. Each row in the DB still represents one physical card.

---

## Architecture

Each detected card crop remains its own DB row. The frontend groups rows by `scryfall_id` (identified) or `name` (unidentified) to produce a `CardGroup` with a count and list of constituent row IDs. The tile renders once per group.

## Data Model

No DB schema changes. A new TypeScript type in the frontend:

```ts
interface CardGroup {
  card: Card;      // representative card (any from the group)
  count: number;   // number of rows in this group
  ids: string[];   // all row IDs in this group (for delete targeting)
}
```

Grouping happens inside `useLibrary` as a derived `groups` value alongside the existing filtered `cards` array.

## Backend — New Endpoint

```
POST /api/cards/{card_id}/copy → 201 Card
```

Duplicates the row: copies all Scryfall metadata fields, assigns a new UUID, keeps the same `source_image`. Used when the user presses `+`.

## Frontend — Interaction

- **`−`**: Calls `DELETE /api/cards/{id}` on one ID from `ids`. Optimistically removes that ID from local state. When the group's count reaches 0, the tile disappears.
- **`+`**: Calls `POST /api/cards/{id}/copy`. Optimistically increments count. Adds the returned new card's ID to the group's `ids`.

## UI Changes

- `CardTile` loses the standalone delete button.
- A small count badge appears at the bottom-right corner of every tile.
- On hover, the badge expands into an inline `− N +` stepper.
- Count = 1: stepper still shows; pressing `−` deletes the card (count → 0 removes tile).
- Both operations update local state optimistically (no full refetch).

## Grouping

- Grouping lives in `useLibrary` — no new component.
- `total` in the Library header continues to reflect total unique groups (not raw rows).
- Filters and search operate on `CardGroup[]`, matching against the representative card's fields.
- The `overrides` map in `LibraryPage` (used by the Fix Card flow) applies to the representative card of a group.

## Scope

- Tile view only for now (grid view can follow the same pattern later).
- No server-side grouping — all grouping is client-side.
