export type CardStatus = "processing" | "identified" | "unidentified";

export interface Card {
  id: string;
  name: string | null;
  scryfall_id: string | null;
  image_url: string | null;
  colors: string | null;        // JSON string e.g. '["R","G"]'
  color_identity: string | null;
  type_line: string | null;
  mana_cost: string | null;
  oracle_text: string | null;
  status: CardStatus;
  created_at: string;
  source_image: string;
}

export interface UploadResponse {
  job_id: string;
  queued: number;
}

export interface SSECardEvent {
  card_id: string;
  name: string | null;
  status: CardStatus;
  image_url: string | null;
  done?: boolean;
}
