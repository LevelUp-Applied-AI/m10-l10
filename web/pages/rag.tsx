import { useState } from "react";

// TODO: import { RAGResponse } from "../lib/types".
import { RAGResponse } from "../lib/types";
import React from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RagPage() {
  const [question, setQuestion] = useState("");
  // TODO: track result + error state + loading.
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    // TODO:
    // 1. POST to `${API_URL}/rag/answer` with JSON body { question, k: 4 }.
    // 2. Handle 422 + 503 distinctly.
    // 3. Render the answer + inline [N] citation markers. Each citation
    //    marker element MUST have `data-testid="citation-marker"` so
    //    Playwright can locate it.
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/rag/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, k: 4 }),
      });
      if (res.status === 422) {
        setError("Validation Error");
        return;
      }
      if (res.status === 503) {
        setError("The backend is starting up — please try again in a moment.");
        return;
      }
      if (!res.ok) {
        setError("Could not reach the backend.");
        return;
      }
      const data: RAGResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  function renderAnswer(answer: string) {
    const regex = /\[(\d+)\]/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(answer)) !== null) {
      if (match.index > lastIndex) {
        parts.push(<span key={lastIndex}>{answer.slice(lastIndex, match.index)}</span>);
      }
      parts.push(
        <sup key={match.index} data-testid="citation-marker">
          [{match[1]}]
        </sup>
      );
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < answer.length) {
      parts.push(<span key={lastIndex}>{answer.slice(lastIndex)}</span>);
    }
    return parts;
  }

  return (
    <main>
      <h1>RAG — Cited Answer</h1>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a recipe question..."
      />
      <button onClick={submit} disabled={!question}>Ask</button>
      {/* TODO: render answer + citations with data-testid markers. */}
      {loading && <p>Loading...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {result && (
        <div>
          <h2>Answer (Confidence: {result.confidence.toFixed(2)})</h2>
          <p>{renderAnswer(result.answer)}</p>
          {result.citations.length > 0 && (
            <div>
              <h3>Citations</h3>
              <ul>
                {result.citations.map((c, i) => (
                  <li key={i}>
                    [Chunk {c.chunk_id}] (Score: {c.score.toFixed(2)})
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
