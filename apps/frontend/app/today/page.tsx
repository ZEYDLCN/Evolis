"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import Heatmap from "../../components/Heatmap";
import OnboardingChecklist from "../../components/OnboardingChecklist";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Entry, EntryInsight, HeatmapDay, OnboardingStatus, Streak } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input, Textarea } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { useLang } from "../../components/LangProvider";
import { cn } from "../../lib/cn";

const STATUS_TONE: Record<string, "positive" | "negative" | "neutral"> = {
  done: "positive",
  partial: "neutral",
  blocked: "negative",
  none: "neutral",
};

const PROMPT_CHIPS = ["What did you learn?", "What did you build?", "What blocked you?", "What are you proud of?"];

const STATUS_OPTIONS = ["done", "partial", "blocked", "none"];

/** Editable AI Extraction (section 20): lets the user correct the topics
 * and completion status the extractor guessed. The correction is stored
 * as ExtractionFeedback (src/database/models.py) for a future eval pass —
 * see section 21 — never silently discarded. */
function EntryCard({ entry, onSaved }: { entry: Entry; onSaved: (updated: Entry) => void }) {
  const [editing, setEditing] = useState(false);
  const [topics, setTopics] = useState(((entry.extraction as { topics?: string[] } | null)?.topics || []).join(", "));
  const [status, setStatus] = useState(entry.completion_status || "none");
  const [saving, setSaving] = useState(false);

  const currentTopics = (entry.extraction as { topics?: string[] } | null)?.topics || [];

  async function save() {
    setSaving(true);
    try {
      const updated = await api.correctEntry(entry.id, {
        topics: topics
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        completion_status: status === "none" ? null : status,
      });
      onSaved(updated);
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-xs text-muted">{new Date(entry.entry_date).toLocaleDateString()}</span>
        <div className="flex items-center gap-2">
          <Badge tone={STATUS_TONE[entry.completion_status || "none"]}>{entry.completion_status || "none"}</Badge>
          <button onClick={() => setEditing((v) => !v)} className="text-xs font-medium text-muted hover:text-brand-emerald">
            {editing ? "Cancel" : "Edit"}
          </button>
        </div>
      </div>
      <p className="text-sm text-ink">{entry.raw_text}</p>

      {!editing && currentTopics.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {currentTopics.map((t) => (
            <Badge key={t}>{t}</Badge>
          ))}
        </div>
      )}

      {editing && (
        <div className="mt-3 space-y-2.5 border-t border-line pt-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-muted">Topics (comma-separated)</label>
            <Input value={topics} onChange={(e) => setTopics(e.target.value)} placeholder="LangGraph, RAG, Docker" />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full rounded-xl border border-line bg-card px-3.5 py-2.5 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand-emerald/30"
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <Button onClick={save} disabled={saving}>
            {saving ? "Saving..." : "Save correction"}
          </Button>
        </div>
      )}
    </Card>
  );
}

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
  const { t } = useLang();
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
      <PageHeader title={t("today.title")} action={streak && <StreakBadge streak={streak} />} />
      <p className="-mt-4 mb-6 text-sm text-muted">{t("today.description")}</p>

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
          placeholder="What happened today? Bugün 45 dakika İngilizce çalıştım, 30 dakika yürüdüm, 2 saat proje geliştirdim..."
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
            {submitting ? t("common.loading") : t("today.saveEntry")}
          </Button>
        </div>
      </Card>

      {lastInsight && (
        <div className="mb-6">
          <InsightCelebration insight={lastInsight} />
        </div>
      )}

      <div className="mb-3 text-sm font-semibold text-ink">{t("today.recentEntries")}</div>
      {loading ? (
        <p className="text-sm text-muted">Loading...</p>
      ) : entries.length === 0 ? (
        <p className="text-sm text-muted">No entries yet — write your first one above.</p>
      ) : (
        <div className="space-y-3">
          {entries.map((e) => (
            <EntryCard
              key={e.id}
              entry={e}
              onSaved={(updated) => setEntries((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))}
            />
          ))}
        </div>
      )}
    </AppShell>
  );
}
