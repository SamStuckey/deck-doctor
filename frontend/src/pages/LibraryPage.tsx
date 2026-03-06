import { useState } from "react";
import { useLibrary } from "../hooks/useLibrary";
import SearchBar from "../components/SearchBar";
import ColorFilter from "../components/ColorFilter";
import TypeFilter from "../components/TypeFilter";
import LibraryTileView from "../components/LibraryTileView";
import LibraryGridView from "../components/LibraryGridView";
import FixCardModal from "../components/FixCardModal";
import { deleteCard } from "../api/client";
import type { Card } from "../types";

type View = "tile" | "grid";

export default function LibraryPage() {
  const {
    cards, total, loading,
    search, setSearch,
    colorFilter, setColorFilter,
    typeFilter, setTypeFilter,
  } = useLibrary();

  const [view, setView] = useState<View>("tile");
  const [fixingCard, setFixingCard] = useState<Card | null>(null);
  const [overrides, setOverrides] = useState<Record<string, Card>>({});
  const [deletedIds, setDeletedIds] = useState<Set<string>>(new Set());

  const displayCards = cards
    .filter((c) => !deletedIds.has(c.id))
    .map((c) => overrides[c.id] ?? c);

  function handleFixed(updated: Card) {
    setOverrides((prev) => ({ ...prev, [updated.id]: updated }));
    setFixingCard(null);
  }

  async function handleDelete(card: Card) {
    try {
      await deleteCard(card.id);
      setDeletedIds((prev) => new Set(prev).add(card.id));
    } catch {
      // silently ignore — card stays visible if delete fails
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
        <LibraryTileView cards={displayCards} onFix={setFixingCard} onDelete={handleDelete} />
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
