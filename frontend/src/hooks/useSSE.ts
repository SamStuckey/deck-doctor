import { useEffect, useState } from "react";
import { createSSEConnection } from "../api/client";
import type { SSECardEvent } from "../types";

export function useSSE(jobId: string | null) {
  const [events, setEvents] = useState<SSECardEvent[]>([]);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!jobId) return;
    setEvents([]);
    setDone(false);

    const es = createSSEConnection(jobId);
    es.onmessage = (e) => {
      const data: SSECardEvent = JSON.parse(e.data);
      if (data.done) {
        setDone(true);
        es.close();
      } else {
        setEvents((prev) => [...prev, data]);
      }
    };
    es.onerror = () => { setDone(true); es.close(); };

    return () => es.close();
  }, [jobId]);

  return { events, done };
}
