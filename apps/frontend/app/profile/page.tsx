"use client";

import { useEffect, useState } from "react";
import NavBar from "../../components/NavBar";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Version, ApiError } from "../../lib/api";
import { page, card, input, button, mutedText, errorText } from "../../lib/styles";

function isoMonthsAgo(months: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString().slice(0, 10);
}

export default function ProfilePage() {
  const ready = useRequireAuth();
  const [versions, setVersions] = useState<Version[]>([]);
  const [start, setStart] = useState(isoMonthsAgo(1));
  const [end, setEnd] = useState(new Date().toISOString().slice(0, 10));
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      setVersions(await api.listVersions());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setGenerating(true);
    try {
      await api.generateVersion(start, end);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to generate version");
    } finally {
      setGenerating(false);
    }
  }

  if (!ready) return null;

  return (
    <>
      <NavBar />
      <main style={page}>
        <h1>Profile</h1>
        <p style={mutedText}>Version snapshots of you — the basis for Diff and Release Notes.</p>

        <form onSubmit={generate} style={card}>
          <strong>Generate a new version</strong>
          <div style={{ display: "flex", gap: 12, marginTop: 12, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 140 }}>
              <label style={{ fontSize: 13, color: "#666" }}>Period start</label>
              <input style={input} type="date" value={start} onChange={(e) => setStart(e.target.value)} />
            </div>
            <div style={{ flex: 1, minWidth: 140 }}>
              <label style={{ fontSize: 13, color: "#666" }}>Period end</label>
              <input style={input} type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
            </div>
          </div>
          <button type="submit" style={{ ...button, marginTop: 12 }} disabled={generating}>
            {generating ? "Generating..." : "Generate version"}
          </button>
          {error && <p style={errorText}>{error}</p>}
        </form>

        <h2 style={{ fontSize: 18, marginTop: "2rem" }}>Versions</h2>
        {loading ? (
          <p style={mutedText}>Loading...</p>
        ) : versions.length === 0 ? (
          <p style={mutedText}>No versions yet — generate one above.</p>
        ) : (
          versions.map((v) => (
            <div key={v.id} style={{ ...card, display: "flex", justifyContent: "space-between" }}>
              <strong>YOU v{v.label}</strong>
              <span style={mutedText}>
                {v.period_start} → {v.period_end}
              </span>
            </div>
          ))
        )}
      </main>
    </>
  );
}
