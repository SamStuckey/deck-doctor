import type { Card, UploadResponse } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function uploadImages(files: File[]): Promise<UploadResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function fetchCards(): Promise<Card[]> {
  const res = await fetch(`${BASE}/api/cards`);
  if (!res.ok) throw new Error("Failed to fetch cards");
  return res.json();
}

export async function fixCard(cardId: string, name: string): Promise<Card> {
  const res = await fetch(`${BASE}/api/cards/${cardId}/fix`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!res.ok) throw new Error("Fix failed");
  return res.json();
}

export function createSSEConnection(jobId: string): EventSource {
  return new EventSource(`${BASE}/api/events/${jobId}`);
}
