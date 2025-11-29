"use client";
import { useState } from "react";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleSend = async () => {
    if (!file || !prompt) return;
    setLoading(true);

    try {
      await fetch("/api/dummy", {
        method: "POST",
        body: JSON.stringify({ filename: file.name, prompt }),
        headers: { "Content-Type": "application/json" },
      });

      const data = await new Promise<{ message: string }>((resolve) =>
        setTimeout(
          () =>
            resolve({
              message: `✅ CV "${file.name}" berhasil direview.\nSaran: Tambahkan pengalaman proyek backend.\nRekomendasi Job: Backend Engineer di Jakarta.`,
            }),
          2000
        )
      );

      setResult(data.message);
    } catch (err) {
      setResult("❌ Terjadi error saat memproses CV.");
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
    <header className="flex justify-center flex-col items-center mt-24">
      <h1
        className="text-5xl font-extrabold 
                  bg-linear-to-r from-purple-500 via-pink-500 to-blue-500 
                  bg-clip-text text-transparent 
                  drop-shadow-lg tracking-wide"
      >
        Resumflus
      </h1>
      <p
        className="mt-3 
                  text-white
                  bg-clip-text text-md 
                  font-medium tracking-tight"
      >
        AI Agent for CV Enhancement & Job Recommendations
      </p>
    </header>

      <main className="flex flex-col items-center justify-center flex-1 gap-6 py-10">
        {!file && (
          <div className="text-center bg-[#6b21a8] rounded-full">
            <input
              type="file"
              accept="application/pdf"
              onChange={(e) => {
                if (e.target.files) setFile(e.target.files[0]);
              }}
              className="block w-full text-sm text-gray-200
                        file:mr-4 file:py-2 file:px-4
                        file:rounded-full file:border-0
                        file:text-sm file:font-semibold file:text-white
                        file:[background:linear-gradient(to_bottom_right,#6b21a8,#1e3a8a)]
                        hover:file:opacity-90 hover:cursor-pointer"
            />
          </div>
        )}

        {file && (
          <div className="flex items-center gap-2 text-center">
            <h2 className="text-xl font-semibold">📄 {file.name}</h2>
            <button
              onClick={() => {
                setFile(null);
                setPrompt("");
                setResult(null);
              }}
              className="ml-2 text-red-300 hover:text-red-500 hover:cursor-pointer font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {file && (
          <div className="flex flex-col w-96 border border-gray-200 rounded-lg p-3 gap-3 bg-white text-black">
            <textarea
              placeholder="I want review and job recommendations..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
              className="w-full border-none outline-none text-base px-2 resize-none"
            />
            <button
              onClick={handleSend}
              disabled={loading}
              className="px-4 py-2 text-white rounded-md 
                        bg-linear-to-br from-purple-800 to-blue-900 
                        hover:opacity-90 hover:cursor-pointer 
                        disabled:opacity-50 text-sm font-bold"
            >
              {loading ? (
                <span className="flex items-center gap-2 justify-center">
                  <svg
                    className="animate-spin h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    ></circle>
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8H4z"
                    ></path>
                  </svg>
                  Loading...
                </span>
              ) : result ? (
                "Send Again"
              ) : (
                "Send"
              )}
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