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
            <th scope="col" className="py-2 pr-4">Name</th>
            <th scope="col" className="py-2 pr-4">Type</th>
            <th scope="col" className="py-2 pr-4">Color</th>
            <th scope="col" className="py-2 pr-4">Mana Cost</th>
            <th scope="col" className="py-2"></th>
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
