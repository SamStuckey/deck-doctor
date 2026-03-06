import type { Card, UploadResponse } from "../types";

// For REST calls: use VITE_API_URL if set (production), otherwise relative (dev proxy)
const BASE = import.meta.env.VITE_API_URL ?? "";

export async function uploadImages(files: File[]): Promise<UploadResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed (${res.status})`);
  return res.json();
}

export async function fetchCards(): Promise<Card[]> {
  const res = await fetch(`${BASE}/api/cards`);
  if (!res.ok) throw new Error(`Failed to fetch cards (${res.status})`);
  return res.json();
}

export async function fixCard(cardId: string, name: string): Promise<Card> {
  const res = await fetch(`${BASE}/api/cards/${cardId}/fix`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error(`Fix failed (${res.status})`);
  return res.json();
}

export function createSSEConnection(jobId: string): EventSource {
  // Always use relative URL for SSE so it routes through the Vite proxy
  // (EventSource doesn't support CORS well with absolute cross-origin URLs)
  return new EventSource(`/api/events/${jobId}`);
}
