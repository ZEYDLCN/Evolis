"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Goal, GoalSuggestion } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { Progress } from "../../components/ui/Progress";
import { PageHeader } from "../../components/ui/PageHeader";
import { EmptyState } from "../../components/ui/EmptyState";
import { useLang } from "../../components/LangProvider";

function SuggestionCard({ suggestion, onAdd, addLabel }: { suggestion: GoalSuggestion; onAdd: () => void; addLabel: string }) {
  return (
    <Card className="border-brand-emerald/20 bg-brand-lime/10">
      <div className="mb-1 text-sm font-semibold text-ink">{suggestion.title}</div>
      <p className="mb-3 text-xs text-muted">{suggestion.description}</p>
      <Button size="sm" onClick={onAdd}>
        {addLabel}
      </Button>
    </Card>
  );
}

function GoalCard({
  goal,
  onComplete,
  onDelete,
  markDoneLabel,
  removeLabel,
  suggestedLabel,
}: {
  goal: Goal;
  onComplete: () => void;
  onDelete: () => void;
  markDoneLabel: string;
  removeLabel: string;
  suggestedLabel: string;
}) {
  const done = goal.status === "done";
  return (
    <Card>
      <div className="mb-1 flex items-center justify-between">
        <div className={`text-sm font-semibold ${done ? "text-muted line-through" : "text-ink"}`}>{goal.title}</div>
        {goal.source === "suggested" && (
          <Badge tone="info" className="shrink-0">
            {suggestedLabel}
          </Badge>
        )}
      </div>
      {goal.description && <p className="mb-2 text-xs text-muted">{goal.description}</p>}
      {goal.progress_pct !== null && (
        <div className="mb-3">
          <Progress value={goal.progress_pct} max={1} />
          <div className="mt-1 text-xs text-muted">
            {goal.current_value} / {goal.target_value}
          </div>
        </div>
      )}
      {!done && (
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" onClick={onComplete}>
            {markDoneLabel}
          </Button>
          <button onClick={onDelete} className="text-xs text-muted hover:text-red-600">
            {removeLabel}
          </button>
        </div>
      )}
    </Card>
  );
}

export default function GoalsPage() {
  const ready = useRequireAuth();
  const { t } = useLang();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [suggestions, setSuggestions] = useState<GoalSuggestion[]>([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [g, s] = await Promise.all([api.listGoals(), api.goalSuggestions()]);
      setGoals(g);
      setSuggestions(s);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  async function addSuggestion(s: GoalSuggestion) {
    await api.createGoal({
      title: s.title,
      description: s.description,
      metric_key: s.metric_key,
      target_value: s.target_value,
      source: "suggested",
    });
    await load();
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    await api.createGoal({ title });
    setTitle("");
    await load();
  }

  if (!ready) return null;

  const activeGoals = goals.filter((g) => g.status !== "done");
  const doneGoals = goals.filter((g) => g.status === "done");
  // Don't suggest a goal that already has an active, matching-title entry.
  const activeTitles = new Set(activeGoals.map((g) => g.title));
  const freshSuggestions = suggestions.filter((s) => !activeTitles.has(s.title));

  return (
    <AppShell>
      <PageHeader title={t("goals.title")} description={t("goals.description")} />

      <Card className="mb-6">
        <form onSubmit={submit} className="flex gap-3">
          <Input placeholder={t("goals.addPlaceholder")} value={title} onChange={(e) => setTitle(e.target.value)} />
          <Button type="submit" disabled={!title.trim()}>
            {t("common.add")}
          </Button>
        </form>
      </Card>

      {!loading && freshSuggestions.length > 0 && (
        <div className="mb-6">
          <div className="mb-3 text-sm font-semibold text-ink">{t("goals.suggested")}</div>
          <div className="grid gap-3 md:grid-cols-2">
            {freshSuggestions.map((s, i) => (
              <SuggestionCard key={i} suggestion={s} onAdd={() => addSuggestion(s)} addLabel={t("goals.addAsGoal")} />
            ))}
          </div>
        </div>
      )}

      <div className="mb-3 text-sm font-semibold text-ink">{t("goals.active")}</div>
      {loading ? (
        <p className="text-sm text-muted">{t("common.loading")}</p>
      ) : activeGoals.length === 0 ? (
        <EmptyState icon="🎯" title={t("goals.noActive")} />
      ) : (
        <div className="mb-6 space-y-3">
          {activeGoals.map((g) => (
            <GoalCard
              key={g.id}
              goal={g}
              markDoneLabel={t("goals.markDone")}
              removeLabel={t("goals.remove")}
              suggestedLabel={t("goals.suggested")}
              onComplete={async () => {
                await api.completeGoal(g.id);
                await load();
              }}
              onDelete={async () => {
                await api.deleteGoal(g.id);
                await load();
              }}
            />
          ))}
        </div>
      )}

      {doneGoals.length > 0 && (
        <>
          <div className="mb-3 text-sm font-semibold text-ink">{t("goals.completed")}</div>
          <div className="space-y-3">
            {doneGoals.map((g) => (
              <GoalCard
                key={g.id}
                goal={g}
                markDoneLabel={t("goals.markDone")}
                removeLabel={t("goals.remove")}
                suggestedLabel={t("goals.suggested")}
                onComplete={() => {}}
                onDelete={async () => {
                  await api.deleteGoal(g.id);
                  await load();
                }}
              />
            ))}
          </div>
        </>
      )}
    </AppShell>
  );
}
