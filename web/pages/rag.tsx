import { Fragment, useState } from "react";

import { RAGResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Split an answer string on [N] citation markers, returning React nodes
// where each marker is wrapped in a span carrying the test id the
// Playwright smoke test looks for.
function renderWithCitations(answer: string) {
  const parts = answer.split(/(\[\d+\])/g);
  return parts.map((part, i) =>
    /^\[\d+\]$/.test(part) ? (
      <span key={i} data-testid="citation-marker">
        {part}
      </span>
    ) : (
      <Fragment key={i}>{part}</Fragment>
    ),
  );
}

export default function RagPage() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
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
        const body = await res.json();
        setError(typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail));
        return;
      }
      if (res.status === 503) {
        setError("The backend is starting up — please try again in a moment.");
        return;
      }
      if (!res.ok) {
        setError(`Request failed (${res.status}).`);
        return;
      }
      const data: RAGResponse = await res.json();
      setResult(data);
    } catch {
      setError("Could not reach the backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>RAG — Cited Answer</h1>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a recipe question..."
      />
      <button onClick={submit} disabled={!question || loading}>Ask</button>
      {loading && <p>Thinking…</p>}
      {error && <p role="alert">{error}</p>}
      {result && (
        <>
          <p>{renderWithCitations(result.answer)}</p>
          <p>Confidence: {result.confidence.toFixed(2)}</p>
          <ul>
            {result.citations.map((c, i) => (
              <li key={i}>
                chunk {c.chunk_id} — score {c.score.toFixed(2)}
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  );
}
