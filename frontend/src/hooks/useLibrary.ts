import { useEffect, useMemo, useState } from "react";
import Fuse from "fuse.js";
import { fetchCards } from "../api/client";
import type { Card } from "../types";

export function useLibrary() {
  const [allCards, setAllCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [colorFilter, setColorFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);

  useEffect(() => {
    fetchCards()
      .then(setAllCards)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const fuse = useMemo(
    () => new Fuse(allCards, { keys: ["name"], threshold: 0.4 }),
    [allCards]
  );

  const cards = useMemo(() => {
    let result = search
      ? fuse.search(search).map((r) => r.item)
      : allCards;

    if (colorFilter) {
      if (colorFilter === "Colorless") {
        result = result.filter((c) => {
          const colors: string[] = c.colors ? JSON.parse(c.colors) : [];
          return colors.length === 0;
        });
      } else if (colorFilter === "Multicolor") {
        result = result.filter((c) => {
          const colors: string[] = c.colors ? JSON.parse(c.colors) : [];
          return colors.length > 1;
        });
      } else {
        result = result.filter((c) => {
          const colors: string[] = c.colors ? JSON.parse(c.colors) : [];
          return colors.includes(colorFilter) && colors.length === 1;
        });
      }
    }

    if (typeFilter) {
      result = result.filter((c) => c.type_line?.includes(typeFilter) ?? false);
    }

    return result;
  }, [allCards, search, colorFilter, typeFilter, fuse]);

  return {
    cards,
    total: allCards.length,
    loading,
    search, setSearch,
    colorFilter, setColorFilter,
    typeFilter, setTypeFilter,
  };
}
