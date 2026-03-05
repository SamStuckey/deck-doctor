const COLORS = [
  { key: "W", label: "White", className: "bg-yellow-50 text-gray-900" },
  { key: "U", label: "Blue", className: "bg-blue-600 text-white" },
  { key: "B", label: "Black", className: "bg-gray-900 text-white border border-gray-600" },
  { key: "R", label: "Red", className: "bg-red-600 text-white" },
  { key: "G", label: "Green", className: "bg-green-700 text-white" },
  { key: "Colorless", label: "Colorless", className: "bg-gray-500 text-white" },
  { key: "Multicolor", label: "Multi", className: "bg-gradient-to-r from-yellow-400 to-blue-500 text-white" },
];

interface Props {
  value: string | null;
  onChange: (v: string | null) => void;
}

export default function ColorFilter({ value, onChange }: Props) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by color">
      {COLORS.map((c) => (
        <button
          key={c.key}
          onClick={() => onChange(value === c.key ? null : c.key)}
          aria-pressed={value === c.key}
          className={`px-3 py-1 rounded-full text-xs font-semibold transition-opacity ${c.className} ${
            value && value !== c.key ? "opacity-40" : "opacity-100"
          }`}
        >
          {c.label}
        </button>
      ))}
    </div>
  );
}
