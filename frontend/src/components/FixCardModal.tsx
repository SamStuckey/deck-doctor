import { useState, useEffect } from "react";
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

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const updated = await fixCard(card.id, name.trim());
      onFixed(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Card not found on Scryfall. Check the name and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="fix-modal-title"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-sm"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="fix-modal-title" className="text-lg font-bold mb-4">Fix Card Name</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            autoFocus
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Card name..."
            aria-label="Card name"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-amber-500"
          />
          {error && <p className="text-red-400 text-xs" role="alert">{error}</p>}
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
