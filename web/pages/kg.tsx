import { useState } from "react";

// TODO: import { KGResponse } from "../lib/types".
import { KGResponse } from "../lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function KgPage() {
  const [question, setQuestion] = useState("");
  // TODO: track result + error state.
  const [result, setResult] = useState<KGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<string[]>([]);

  async function submit() {
    // TODO:
    // 1. POST to `${API_URL}/kg/query` with JSON body { question }.
    // 2. Handle 422 (unsupported question) — surface the supported_patterns
    //    list to the user from the response detail.
    // 3. Render the cypher and table of rows.
    setError(null);
    setResult(null);
    setPatterns([]);
    try {
      const res = await fetch(`${API_URL}/kg/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (res.status === 422) {
        const data = await res.json();
        setError("Unsupported question");
        if (data.detail && data.detail.supported_patterns) {
          setPatterns(data.detail.supported_patterns);
        }
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
      const data: KGResponse = await res.json();
      setResult(data);
    } catch (err) {
      setError("Could not reach the backend.");
    }
  }

  return (
    <main>
      <h1>Knowledge Graph — Recipe Query</h1>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="e.g. Find Sichuan recipes"
      />
      <button onClick={submit} disabled={!question}>Ask</button>
      {/* TODO: render cypher in a <pre>, rows in a <table> with each
                row having `data-testid="kg-row"`. */}
      {error && (
        <div style={{ color: "red" }}>
          <p>{error}</p>
          {patterns.length > 0 && (
            <ul>
              {patterns.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      {result && (
        <div>
          <h2>Cypher</h2>
          <pre>{result.cypher}</pre>
          <h2>Results ({result.count})</h2>
          <table>
            <thead>
              <tr>
                {result.rows.length > 0 && Object.keys(result.rows[0]).map((k) => (
                  <th key={k}>{k}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {result.rows.map((row, i) => (
                <tr key={i} data-testid="kg-row">
                  {Object.values(row).map((val, j) => (
                    <td key={j}>{JSON.stringify(val)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
