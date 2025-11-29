"use client";
import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);

    try {
      await fetch("/api/dummy", {
        method: "POST",
        body: JSON.stringify({ filename: file.name }),
        headers: { "Content-Type": "application/json" },
      });

      const data = await new Promise<{ message: string }>((resolve) =>
        setTimeout(
          () =>
            resolve({
              message: `✅ CV "${file.name}" uploaded successfully.\nFeedback: Add backend project experience.\nJob Recommendation: Backend Engineer in Jakarta.`,
            }),
          2000
        )
      );

      setResult(data.message);
    } catch (err) {
      setResult("❌ Error while uploading CV.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="flex flex-col min-h-screen text-white relative overflow-hidden"
      style={{
        backgroundImage: `
          radial-gradient(circle at 20% 30%, rgba(139,92,246,0.4), transparent 40%),
          radial-gradient(circle at 80% 20%, rgba(59,130,246,0.4), transparent 40%),
          radial-gradient(circle at 50% 80%, rgba(99,102,241,0.4), transparent 40%),
          linear-gradient(to bottom right, #6b21a8, #1e3a8a)
        `,
      }}
    >
      <header className="flex justify-center flex-col items-center mt-12">
        <h1
          className="text-5xl font-extrabold 
                     bg-linear-to-r from-purple-500 via-pink-500 to-blue-500 
                     bg-clip-text text-transparent 
                     drop-shadow-lg tracking-wide"
        >
          Resumflus
        </h1>
        <p className="mt-3 text-white text-md font-medium tracking-tight">
          AI Agent for CV Enhancement & Job Recommendations
        </p>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center gap-6">
        {!file && (
          <div
            className="w-96 h-40 flex items-center justify-center border-2 border-dashed border-purple-400 rounded-lg cursor-pointer bg-white/10 hover:bg-white/20"
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                setFile(e.dataTransfer.files[0]);
              }
            }}
          >
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => {
                if (e.target.files) setFile(e.target.files[0]);
              }}
              className="hidden"
              id="fileInput"
            />
            <label htmlFor="fileInput" className="text-center text-sm text-white">
              Drag & drop your CV here or click to select (PDF only)
            </label>
          </div>
        )}

        {file && (
          <div className="flex flex-col items-center gap-3">
            <div className="flex items-center gap-2 text-center">
              <h2 className="text-xl font-semibold">📄 {file.name}</h2>
              <button
                onClick={() => {
                  setFile(null);
                  setResult(null);
                }}
                className="ml-2 text-red-300 hover:text-red-500 hover:cursor-pointer font-bold"
              >
                ✕
              </button>
            </div>

            <button
              onClick={handleUpload}
              disabled={loading}
              className="px-4 py-2 text-white rounded-md 
                         bg-linear-to-br from-purple-800 to-blue-900 
                         hover:opacity-90 hover:cursor-pointer 
                         disabled:opacity-50 text-sm font-bold"
            >
              {loading ? "Processing..." : result ? "Review Again" : "Start Review"}
            </button>
          </div>
        )}

        {result && (
          <div className="w-96 border border-green-300 bg-green-50 rounded-lg p-4 text-left whitespace-pre-line text-black">
            {result}
          </div>
        )}
      </main>

      <footer className="w-full bg-opacity-30 text-gray-200 py-4 text-center">
        <p className="text-sm">© 2025 Resumflus. All rights reserved.</p>
      </footer>
    </div>
  );
}