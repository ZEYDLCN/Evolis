"use client";

import { useEffect, useState } from "react";
import NavBar from "../../components/NavBar";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Entry } from "../../lib/api";
import { page, card, input, button, brand, mutedText, pill } from "../../lib/styles";

const STATUS_COLOR: Record<string, string> = {
  done: "#E3F3EA",
  partial: "#FFF4E0",
  blocked: "#FBE7E7",
  none: brand.surfaceTint,
};

export default function TodayPage() {
  const ready = useRequireAuth();
  const [text, setText] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadEntries() {
    setLoading(true);
    try {
      setEntries(await api.listEntries());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ready) loadEntries();
  }, [ready]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setSubmitting(true);
    try {
      await api.addEntry(text);
      setText("");
      await loadEntries();
    } finally {
      setSubmitting(false);
    }
  }

  if (!ready) return null;

  return (
    <>
      <NavBar />
      <main style={page}>
        <h1>Today</h1>
        <p style={mutedText}>What did you do today? Write it in one paragraph — Evolis extracts the structure.</p>

        <form onSubmit={submit} style={card}>
          <textarea
            style={{ ...input, minHeight: 100, resize: "vertical", fontFamily: "inherit" }}
            placeholder="Bugün 2 saat LangGraph çalıştım, RAG pipeline geliştirdim..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <div style={{ marginTop: 12 }}>
            <button type="submit" style={button} disabled={submitting || !text.trim()}>
              {submitting ? "Saving..." : "Save entry"}
            </button>
          </div>
        </form>

        <h2 style={{ fontSize: 18, marginTop: "2rem" }}>Recent entries</h2>
        {loading ? (
          <p style={mutedText}>Loading...</p>
        ) : entries.length === 0 ? (
          <p style={mutedText}>No entries yet — write your first one above.</p>
        ) : (
          entries.map((e) => (
            <div key={e.id} style={card}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={mutedText}>{new Date(e.entry_date).toLocaleDateString()}</span>
                <span
                  style={{
                    ...pill,
                    background: STATUS_COLOR[e.completion_status || "none"],
                  }}
                >
                  {e.completion_status || "none"}
                </span>
              </div>
              <p style={{ margin: 0 }}>{e.raw_text}</p>
              {e.extraction && Array.isArray((e.extraction as { topics?: string[] }).topics) && (
                <div style={{ marginTop: 10 }}>
                  {((e.extraction as { topics?: string[] }).topics || []).map((t) => (
                    <span key={t} style={pill}>
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </main>
    </>
  );
}
