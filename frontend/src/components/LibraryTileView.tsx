import type { Card } from "../types";
import CardTile from "./CardTile";

interface Props {
  cards: Card[];
  onFix: (card: Card) => void;
  onDelete: (card: Card) => void;
}

export default function LibraryTileView({ cards, onFix, onDelete }: Props) {
  if (!cards.length) {
    return <p className="text-gray-500 text-sm py-8 text-center">No cards found.</p>;
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-3">
      {cards.map((card, index) => (
        <CardTile key={card.id} card={card} onFix={onFix} onDelete={onDelete} eager={index < 8} />
      ))}
    </div>
  );
}
