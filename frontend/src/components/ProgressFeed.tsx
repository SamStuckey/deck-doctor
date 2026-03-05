import type { SSECardEvent } from "../types";

interface Props {
  events: SSECardEvent[];
  done: boolean;
}

export default function ProgressFeed({ events, done }: Props) {
  if (!events.length && !done) return null;

  return (
    <div className="mt-6 space-y-2">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">
        Processing
      </h3>
      <ul className="space-y-1">
        {events.map((e) => (
          <li key={e.card_id} className="flex items-center gap-2 text-sm">
            {e.status === "identified" ? (
              <span className="text-green-400" aria-hidden="true">✓</span>
            ) : (
              <span className="text-red-400" aria-hidden="true">✗</span>
            )}
            <span className={e.status === "identified" ? "text-gray-200" : "text-gray-500"}>
              {e.name ?? "Unidentified card"}
            </span>
          </li>
        ))}
      </ul>
      {done && (
        <p className="text-sm text-amber-400 mt-3">
          Done — {events.filter((e) => e.status === "identified").length} of{" "}
          {events.length} identified
        </p>
      )}
    </div>
  );
}
