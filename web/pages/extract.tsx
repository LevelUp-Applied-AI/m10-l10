import { useState } from "react";

import { ExtractResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExtractPage() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/extract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
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
      const data: ExtractResponse = await res.json();
      setResult(data);
    } catch {
      setError("Could not reach the backend.");
    }
  }

  return (
    <main>
      <h1>Extract — Named Entity Recognition</h1>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={submit} disabled={!text}>Extract</button>
      {error && <p role="alert">{error}</p>}
      {result && (
        <ul>
          {result.entities.map((ent, i) => (
            <li key={i} data-testid="entity-span">
              <strong>{ent.text}</strong> — {ent.label} ({ent.start}–{ent.end})
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
