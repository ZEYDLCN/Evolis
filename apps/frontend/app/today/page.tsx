"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import Heatmap from "../../components/Heatmap";
import OnboardingChecklist from "../../components/OnboardingChecklist";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Entry, EntryInsight, HeatmapDay, OnboardingStatus, Streak } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Textarea } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { cn } from "../../lib/cn";

const STATUS_TONE: Record<string, "positive" | "negative" | "neutral"> = {
  done: "positive",
  partial: "neutral",
  blocked: "negative",
  none: "neutral",
};

const PROMPT_CHIPS = ["What did you learn?", "What did you build?", "What blocked you?", "What are you proud of?"];

function StreakBadge({ streak }: { streak: Streak }) {
  if (streak.current_streak === 0) return null;
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-brand-lime/30 px-3.5 py-1.5 text-sm font-bold text-brand-forest">
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
    const ord = t.mentions_this_week === 2 ? "nd" : t.mentions_this_week === 3 ? "rd" : "th";
    lines.push(`🔁 ${t.topic} — this is your ${t.mentions_this_week}${ord} mention this week.`);
  }
  for (const t of insight.new_topics) {
    lines.push(`✨ New topic detected → ${t}`);
  }

  return (
    <Card className="border-brand-emerald/20 bg-brand-lime/10">
      <div className="mb-1 text-sm font-semibold text-brand-emerald">Entry analyzed ✓</div>
      {lines.map((line, i) => (
        <div key={i} className={cn("py-0.5 text-sm text-ink", i === 0 && "font-semibold")}>
          {line}
        </div>
      ))}
    </Card>
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

  async function submitText(value: string) {
    if (!value.trim()) return;
    setSubmitting(true);
    try {
      const created = await api.addEntry(value);
      setText("");
      setLastInsight(created.insight ?? null);
      await loadAll();
    } finally {
      setSubmitting(false);
    }
  }

  function usePromptChip(prompt: string) {
    setText((prev) => (prev ? prev : prompt.replace("?", "") + ": "));
  }

  if (!ready) return null;

  return (
    <AppShell>
      <PageHeader title="Today" action={streak && <StreakBadge streak={streak} />} />
      <p className="-mt-4 mb-6 text-sm text-muted">Tell Evolis what you worked on, learned, completed, or struggled with.</p>

      {heatmap.length > 0 && (
        <Card className="mb-6">
          <Heatmap days={heatmap} />
        </Card>
      )}

      {onboarding && (
        <div className="mb-6">
          <OnboardingChecklist status={onboarding} />
        </div>
      )}

      <Card className="mb-6">
        <Textarea
          className="min-h-[110px]"
          placeholder="What happened today? Bugün 2 saat LangGraph çalıştım, RAG pipeline geliştirdim..."
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="mt-3 flex flex-wrap gap-2">
          {PROMPT_CHIPS.map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => usePromptChip(chip)}
              className="rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
            >
              {chip}
            </button>
          ))}
        </div>
        <div className="mt-4">
          <Button onClick={() => submitText(text)} disabled={submitting || !text.trim()}>
            {submitting ? "Saving..." : "Save entry"}
          </Button>
        </div>
      </Card>

      {lastInsight && (
        <div className="mb-6">
          <InsightCelebration insight={lastInsight} />
        </div>
      )}

      <div className="mb-3 text-sm font-semibold text-ink">Recent entries</div>
      {loading ? (
        <p className="text-sm text-muted">Loading...</p>
      ) : entries.length === 0 ? (
        <p className="text-sm text-muted">No entries yet — write your first one above.</p>
      ) : (
        <div className="space-y-3">
          {entries.map((e) => (
            <Card key={e.id}>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs text-muted">{new Date(e.entry_date).toLocaleDateString()}</span>
                <Badge tone={STATUS_TONE[e.completion_status || "none"]}>{e.completion_status || "none"}</Badge>
              </div>
              <p className="text-sm text-ink">{e.raw_text}</p>
              {e.extraction && Array.isArray((e.extraction as { topics?: string[] }).topics) && (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {((e.extraction as { topics?: string[] }).topics || []).map((t) => (
                    <Badge key={t}>{t}</Badge>
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
