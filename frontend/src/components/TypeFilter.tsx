const TYPES = ["Creature", "Instant", "Sorcery", "Enchantment", "Artifact", "Planeswalker", "Land"];

interface Props {
  value: string | null;
  onChange: (v: string | null) => void;
}

export default function TypeFilter({ value, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by type">
      {TYPES.map((t) => (
        <button
          key={t}
          onClick={() => onChange(value === t ? null : t)}
          aria-pressed={value === t}
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
