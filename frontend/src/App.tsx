import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import LibraryPage from "./pages/LibraryPage";

type Tab = "upload" | "library";

function getInitialTab(): Tab {
  return window.location.hash === "#library" ? "library" : "upload";
}

export default function App() {
  const [tab, setTab] = useState<Tab>(getInitialTab);

  function navigate(next: Tab) {
    window.location.hash = next;
    setTab(next);
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <nav role="tablist" className="border-b border-gray-800 px-6 py-4 flex items-center gap-8">
        <span className="font-bold text-xl text-amber-400">Deck Doctor</span>
        <button
          role="tab"
          aria-selected={tab === "upload"}
          onClick={() => navigate("upload")}
          className={`text-sm font-medium pb-1 border-b-2 transition-colors ${
            tab === "upload"
              ? "border-amber-400 text-amber-400"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          Upload
        </button>
        <button
          role="tab"
          aria-selected={tab === "library"}
          onClick={() => navigate("library")}
          className={`text-sm font-medium pb-1 border-b-2 transition-colors ${
            tab === "library"
              ? "border-amber-400 text-amber-400"
              : "border-transparent text-gray-400 hover:text-gray-200"
          }`}
        >
          Library
        </button>
      </nav>
      <main className="p-6">
        {tab === "upload" ? (
          <UploadPage onDone={() => navigate("library")} />
        ) : (
          <LibraryPage />
        )}
      </main>
    </div>
  );
}
