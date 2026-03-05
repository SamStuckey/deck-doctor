interface Props {
  value: string;
  onChange: (v: string) => void;
}

export default function SearchBar({ value, onChange }: Props) {
  return (
    <input
      type="search"
      placeholder="Search cards..."
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Search cards"
      className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-amber-500"
    />
  );
}
