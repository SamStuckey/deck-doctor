import { useState } from "react";
import UploadZone from "../components/UploadZone";
import ProgressFeed from "../components/ProgressFeed";
import { uploadImages } from "../api/client";
import { useSSE } from "../hooks/useSSE";

interface Props {
  onDone: () => void;
}

export default function UploadPage({ onDone }: Props) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { events, done } = useSSE(jobId);

  function handleReset() {
    setJobId(null);
    setError(null);
    setUploading(false);
  }

  async function handleFiles(files: File[]) {
    setError(null);
    setUploading(true);
    try {
      const resp = await uploadImages(files);
      setJobId(resp.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Upload Cards</h1>
      <UploadZone onFiles={handleFiles} disabled={uploading || !!jobId} />
      {error && <p className="text-red-400 text-sm mt-3" role="alert">{error}</p>}
      <ProgressFeed events={events} done={done} />
      {done && (
        <div className="mt-6 flex gap-3">
          <button
            onClick={onDone}
            className="px-6 py-2 bg-amber-500 hover:bg-amber-400 text-black font-semibold rounded-lg transition-colors"
          >
            View Library →
          </button>
          <button
            onClick={handleReset}
            className="px-6 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 font-semibold rounded-lg transition-colors"
          >
            Scan More Cards
          </button>
        </div>
      )}
    </div>
  );
}
