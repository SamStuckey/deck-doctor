import type { Card } from "../types";

const PLACEHOLDER =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='280' viewBox='0 0 200 280'%3E%3Crect width='200' height='280' fill='%23374151'/%3E%3Ctext x='100' y='145' text-anchor='middle' fill='%236B7280' font-size='14' font-family='sans-serif'%3E%3F%3C/text%3E%3C/svg%3E";

interface Props {
  card: Card;
  onFix?: (card: Card) => void;
  onDelete?: (card: Card) => void;
  eager?: boolean;
}

export default function CardTile({ card, onFix, onDelete, eager }: Props) {
  return (
    <div className="group relative rounded-lg overflow-hidden bg-gray-900 border border-gray-800 hover:border-amber-500/50 transition-colors">
      <img
        src={card.image_url ?? PLACEHOLDER}
        alt={card.name ?? "Unidentified card"}
        className="w-full object-cover"
        loading={eager ? "eager" : "lazy"}
      />
      {onDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(card); }}
          aria-label={`Delete ${card.name ?? "card"}`}
          className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-red-600 hover:bg-red-500 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity z-10"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="w-3 h-3">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      )}
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
