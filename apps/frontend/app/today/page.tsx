"use client";

import { useEffect, useState } from "react";
import NavBar from "../../components/NavBar";
import Heatmap from "../../components/Heatmap";
import OnboardingChecklist from "../../components/OnboardingChecklist";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Entry, EntryInsight, HeatmapDay, OnboardingStatus, Streak } from "../../lib/api";
import { page, card, input, button, brand, mutedText, pill } from "../../lib/styles";

const STATUS_COLOR: Record<string, string> = {
  done: "#E3F3EA",
  partial: "#FFF4E0",
  blocked: "#FBE7E7",
  none: brand.surfaceTint,
};

function StreakBadge({ streak }: { streak: Streak }) {
  if (streak.current_streak === 0) return null;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "6px 14px",
        borderRadius: 999,
        background: brand.limeTint,
        color: brand.deepForest,
        fontWeight: 700,
        fontSize: 15,
      }}
    >
      🔥 {streak.current_streak} day{streak.current_streak === 1 ? "" : "s"}
    </span>
  );
}

function InsightCelebration({ insight }: { insight: EntryInsight }) {
  const lines: string[] = [];
  if (insight.streak.is_new_best && insight.streak.current > 1) {
    lines.push(`🏆 New personal best — ${insight.streak.current}-day streak!`);
  } else if (insight.streak.current > 1) {
    lines.push(`🔥 ${insight.streak.current}-day streak. Keep it going.`);
  } else {
    lines.push(`🌱 First entry of a new streak.`);
  }
  for (const t of insight.recurring_topics) {
    lines.push(`🔁 ${t.topic} — this is your ${t.mentions_this_week}${t.mentions_this_week === 2 ? "nd" : t.mentions_this_week === 3 ? "rd" : "th"} mention this week.`);
  }
  for (const t of insight.new_topics) {
    lines.push(`✨ New interest showing up: ${t}`);
  }

  return (
    <div style={{ ...card, background: brand.limeTint, border: "none" }}>
      {lines.map((line, i) => (
        <div key={i} style={{ padding: "3px 0", fontWeight: i === 0 ? 700 : 400, color: brand.deepForest }}>
          {line}
        </div>
      ))}
    </div>
  );
}

export default function TodayPage() {
  const ready = useRequireAuth();
  const [text, setText] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [streak, setStreak] = useState<Streak | null>(null);
  const [heatmap, setHeatmap] = useState<HeatmapDay[]>([]);
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [lastInsight, setLastInsight] = useState<EntryInsight | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);

  async function loadAll() {
    setLoading(true);
    try {
      const [e, s, h, o] = await Promise.all([api.listEntries(), api.streak(), api.heatmap(182), api.onboarding()]);
      setEntries(e);
      setStreak(s);
      setHeatmap(h);
      setOnboarding(o);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ready) loadAll();
  }, [ready]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim()) return;
    setSubmitting(true);
    try {
      const created = await api.addEntry(text);
      setText("");
      setLastInsight(created.insight ?? null);
      await loadAll();
    } finally {
      setSubmitting(false);
    }
  }

  if (!ready) return null;

  return (
    <>
      <NavBar />
      <main style={page}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
          <h1 style={{ margin: 0 }}>Today</h1>
          {streak && <StreakBadge streak={streak} />}
        </div>
        <p style={mutedText}>What did you do today? Write it in one paragraph — Evolis extracts the structure.</p>

        {heatmap.length > 0 && (
          <div style={card}>
            <Heatmap days={heatmap} />
          </div>
        )}

        {onboarding && <OnboardingChecklist status={onboarding} />}

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

        {lastInsight && <InsightCelebration insight={lastInsight} />}

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
