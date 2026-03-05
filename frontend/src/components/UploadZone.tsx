import { useRef, useState } from "react";

interface Props {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
}

const MAX = 10;
const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];

export default function UploadZone({ onFiles, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function handle(files: FileList | null) {
    if (!files) return;
    const valid = Array.from(files)
      .filter((f) => ACCEPTED.includes(f.type))
      .slice(0, MAX);
    if (valid.length) onFiles(valid);
  }

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files); }}
      className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-colors ${
        dragging
          ? "border-amber-400 bg-amber-400/10"
          : disabled
          ? "border-gray-700 opacity-50 cursor-not-allowed"
          : "border-gray-700 hover:border-gray-500"
      }`}
    >
      <p className="text-lg font-medium text-gray-300">
        Drop card photos here or click to browse
      </p>
      <p className="text-sm text-gray-500 mt-1">
        Up to {MAX} images • JPG, PNG, WebP
      </p>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED.join(",")}
        multiple
        className="hidden"
        onChange={(e) => handle(e.target.files)}
        disabled={disabled}
      />
    </div>
  );
}
