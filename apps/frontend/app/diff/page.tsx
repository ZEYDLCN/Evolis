"use client";

import { useEffect, useState } from "react";
import NavBar from "../../components/NavBar";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Version, DiffResult, ApiError } from "../../lib/api";
import { page, card, button, mutedText, errorText, pill } from "../../lib/styles";

function pct(x: number | null): string {
  if (x === null) return "—";
  const sign = x >= 0 ? "+" : "";
  return `${sign}${(x * 100).toFixed(0)}%`;
}

export default function DiffPage() {
  const ready = useRequireAuth();
  const [versions, setVersions] = useState<Version[]>([]);
  const [base, setBase] = useState("");
  const [target, setTarget] = useState("");
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [releaseNotes, setReleaseNotes] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ready) return;
    api.listVersions().then((vs) => {
      setVersions(vs);
      if (vs.length >= 2) {
        setBase(vs[0].label);
        setTarget(vs[vs.length - 1].label);
      }
    });
  }, [ready]);

  async function runDiff(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      setDiff(await api.diff(base, target));
      setReleaseNotes(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to compute diff");
      setDiff(null);
    } finally {
      setLoading(false);
    }
  }

  async function loadReleaseNotes() {
    const result = await api.releaseNotes(base, target);
    setReleaseNotes(result.text);
  }

  if (!ready) return null;

  return (
    <>
      <NavBar />
      <main style={page}>
        <h1>Diff</h1>
        <p style={mutedText}>Compare two version snapshots of yourself.</p>

        {versions.length < 2 ? (
          <p style={mutedText}>You need at least two versions to diff — generate them on the Profile page.</p>
        ) : (
          <form onSubmit={runDiff} style={{ ...card, display: "flex", gap: 12, alignItems: "flex-end", flexWrap: "wrap" }}>
            <div>
              <label style={{ fontSize: 13, color: "#666", display: "block" }}>Base</label>
              <select value={base} onChange={(e) => setBase(e.target.value)}>
                {versions.map((v) => (
                  <option key={v.id} value={v.label}>
                    v{v.label}
                  </option>
                ))}
              </select>
            </div>
            <span style={mutedText}>→</span>
            <div>
              <label style={{ fontSize: 13, color: "#666", display: "block" }}>Target</label>
              <select value={target} onChange={(e) => setTarget(e.target.value)}>
                {versions.map((v) => (
                  <option key={v.id} value={v.label}>
                    v{v.label}
                  </option>
                ))}
              </select>
            </div>
            <button type="submit" style={button} disabled={loading}>
              {loading ? "Comparing..." : "Compare"}
            </button>
          </form>
        )}

        {error && <p style={errorText}>{error}</p>}

        {diff && (
          <div style={{ marginTop: "1.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h2 style={{ fontFamily: "monospace", fontSize: 18, margin: 0 }}>
                YOU v{diff.base} → YOU v{diff.target}
              </h2>
              <button onClick={loadReleaseNotes} style={{ ...button, background: "#eee", color: "#333" }}>
                Release Notes
              </button>
            </div>

            {releaseNotes && (
              <pre style={{ ...card, whiteSpace: "pre-wrap", fontFamily: "monospace", fontSize: 14, marginTop: 12 }}>{releaseNotes}</pre>
            )}

            {diff.added_topics.length > 0 && (
              <Section title="Added">
                {diff.added_topics.map((t) => (
                  <span key={t} style={{ ...pill, background: "#e6f4ea" }}>
                    + {t}
                  </span>
                ))}
              </Section>
            )}

            {diff.emerging_topics.length > 0 && (
              <Section title="Emerging Interest">
                {diff.emerging_topics.map((t) => (
                  <span key={t} style={{ ...pill, background: "#e8f0fe" }}>
                    → {t}
                  </span>
                ))}
              </Section>
            )}

            <Section title="Behavior">
              <div style={card}>
                <div>Completion Rate: {pct(diff.completion_change)}</div>
                <div>Deep Work: {pct(diff.deep_work_change)}</div>
                <div>Context Switching: {diff.context_switching_change ?? "—"}/day</div>
              </div>
            </Section>

            {diff.declining_topics.length > 0 && (
              <Section title="Declining">
                {diff.declining_topics.map((t) => (
                  <span key={t} style={{ ...pill, background: "#fff4e0" }}>
                    ↓ {t}
                  </span>
                ))}
              </Section>
            )}

            {diff.dormant_topics.length > 0 && (
              <Section title="Dormant">
                {diff.dormant_topics.map((t) => (
                  <span key={t} style={{ ...pill, background: "#f0f0f0" }}>
                    - {t}
                  </span>
                ))}
              </Section>
            )}

            {Object.keys(diff.skill_changes).length > 0 && (
              <Section title="Skills">
                {Object.entries(diff.skill_changes).map(([skill, change]) => (
                  <div key={skill} style={{ marginBottom: 4 }}>
                    {skill}: {change.before} → {change.after} ({change.change >= 0 ? "+" : ""}
                    {change.change})
                  </div>
                ))}
              </Section>
            )}
          </div>
        )}
      </main>
    </>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "1.25rem" }}>
      <h3 style={{ fontSize: 15, color: "#666", marginBottom: 8 }}>{title}</h3>
      <div>{children}</div>
    </div>
  );
}
