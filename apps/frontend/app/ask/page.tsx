"use client";

import { useState } from "react";
import NavBar from "../../components/NavBar";
import { useRequireAuth } from "../../lib/useAuth";
import { api, AskResult, ApiError } from "../../lib/api";
import { page, card, input, button, mutedText, errorText, pill } from "../../lib/styles";

const SUGGESTIONS = [
  "Son 6 ayda nasıl değiştim?",
  "Hangi konulara ilgim arttı?",
  "Son 3 ayda en fazla zaman ayırdığım teknik alan ne?",
];

export default function AskPage() {
  const ready = useRequireAuth();
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask(q: string) {
    if (!q.trim()) return;
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      setResult(await api.ask(q));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to get an answer");
    } finally {
      setLoading(false);
    }
  }

  if (!ready) return null;

  return (
    <>
      <NavBar />
      <main style={page}>
        <h1>Ask LifeDiff</h1>
        <p style={mutedText}>Ask a question about your own history — every number in the answer is computed, not guessed.</p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(question);
          }}
          style={{ ...card, display: "flex", gap: 12 }}
        >
          <input style={input} placeholder="Son 6 ayda nasıl değiştim?" value={question} onChange={(e) => setQuestion(e.target.value)} />
          <button type="submit" style={button} disabled={loading || !question.trim()}>
            {loading ? "..." : "Ask"}
          </button>
        </form>

        <div style={{ marginBottom: "1.5rem" }}>
          {SUGGESTIONS.map((s) => (
            <span
              key={s}
              onClick={() => {
                setQuestion(s);
                ask(s);
              }}
              style={{ ...pill, background: "#f0f0f0", cursor: "pointer" }}
            >
              {s}
            </span>
          ))}
        </div>

        {error && <p style={errorText}>{error}</p>}

        {result && (
          <div style={card}>
            <div style={{ ...pill, background: "#e8f0fe", marginBottom: 12 }}>{result.query_class}</div>
            <p style={{ fontSize: 16 }}>{result.answer}</p>
            <p style={mutedText}>{result.grounded ? "✓ Grounded in your computed analytics" : ""}</p>
          </div>
        )}
      </main>
    </>
  );
}
