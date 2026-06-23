import { useState } from "react";

// TODO: import { ExtractResponse } from "../lib/types" once you declare it.
import { ExtractResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExtractPage() {
  const [text, setText] = useState("");
  // TODO: track the result as ExtractResponse | null and an error state.
  const [result, setResult] = useState<ExtractResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    // TODO:
    // 1. POST to `${API_URL}/extract` with JSON body { text }.
    // 2. Handle 422 (validation) and 503 (backend not ready) distinctly.
    // 3. Parse the response and put it on state.
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/extract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
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
      const data: ExtractResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError("Could not reach the backend.");
    }
  }

  return (
    <main>
      <h1>Extract — Named Entity Recognition</h1>
      <textarea value={text} onChange={(e) => setText(e.target.value)} />
      <button onClick={submit} disabled={!text}>Extract</button>
      {/* TODO: render entity spans with `data-testid="entity-span"` so
                Playwright can find them. */}
      {error && <p style={{ color: "red" }}>{error}</p>}
      {result && (
        <div>
          <h2>Entities</h2>
          <ul>
            {result.entities.map((ent, i) => (
              <li key={i} data-testid="entity-span">
                {ent.text} ({ent.label}) [{ent.start}, {ent.end}]
              </li>
            ))}
          </ul>
        </div>
      )}
    </main>
  );
}
