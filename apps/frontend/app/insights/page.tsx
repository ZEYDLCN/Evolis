"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Anomaly, Behavior, Pattern, SkillNode, TrendForecastResponse } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { useLang } from "../../components/LangProvider";

const CONFIDENCE_TONE: Record<string, "positive" | "negative" | "neutral" | "info"> = {
  high: "info",
  medium: "neutral",
  low: "neutral",
};

function ConfidenceBadge({ confidence }: { confidence: "low" | "medium" | "high" }) {
  return (
    <Badge tone={CONFIDENCE_TONE[confidence]} className="ml-2 shrink-0 text-[10px] uppercase">
      {confidence} confidence
    </Badge>
  );
}

const DIRECTION_ICON: Record<string, string> = { up: "↑", down: "↓", flat: "→" };

function ForecastRow({ label, unit, forecast }: { label: string; unit: string; forecast: TrendForecastResponse["completion_rate"] }) {
  return (
    <div className="mb-3 last:mb-0">
      <div className="mb-1 flex items-center justify-between text-sm">
        <span className="text-ink">{label}</span>
        <span className="font-mono text-muted">
          {DIRECTION_ICON[forecast.direction]} next week ≈ {forecast.forecast_next}
          {unit}
        </span>
      </div>
      <div className="flex items-end gap-1" style={{ height: 32 }}>
        {forecast.history.map((v, i) => {
          const max = Math.max(...forecast.history, 0.01);
          return <div key={i} className="flex-1 rounded-t bg-brand-emerald/50" style={{ height: `${Math.max(4, (v / max) * 32)}px` }} />;
        })}
      </div>
      <div className="mt-1 text-[10px] uppercase tracking-wide text-muted">{forecast.confidence} confidence projection</div>
    </div>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div className="mb-2.5">
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-ink">{label}</span>
        <span className="text-muted">{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2 rounded-full bg-surface">
        <div className="h-full rounded-full bg-brand-emerald" style={{ width: `${Math.min(value, 1) * 100}%` }} />
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <div className="mb-2 text-sm font-semibold text-ink">{title}</div>
      <Card>{children}</Card>
    </div>
  );
}

const DOMAIN_ICON: Record<string, string> = {
  Skills: "🎯",
  "Work & Projects": "💼",
  Learning: "📚",
  "Habits & Routines": "🔁",
  "Personal Growth": "🌱",
  Behavior: "📊",
};

/** Broader life tracking: the same interest scores as "Interest Drift"
 * used to show, grouped under the five life domains (plus Behavior) —
 * Evolis is meant to track more than just tech skills. */
function DomainGroups({ domains }: { domains: Record<string, Record<string, number>> }) {
  const names = Object.keys(domains);
  if (names.length === 0) return <p className="text-sm text-muted">Not enough data yet.</p>;

  return (
    <div className="space-y-4">
      {names.map((domain) => (
        <div key={domain}>
          <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
            <span>{DOMAIN_ICON[domain] ?? "•"}</span>
            {domain}
          </div>
          {Object.entries(domains[domain]).map(([topic, score]) => (
            <Bar key={topic} label={topic} value={score} />
          ))}
        </div>
      ))}
    </div>
  );
}

export default function InsightsPage() {
  const ready = useRequireAuth();
  const { t } = useLang();
  const [domains, setDomains] = useState<Record<string, Record<string, number>>>({});
  const [skills, setSkills] = useState<SkillNode[]>([]);
  const [behavior, setBehavior] = useState<Behavior | null>(null);
  const [graph, setGraph] = useState<{ nodes: SkillNode[]; edges: { from: string; to: string }[] }>({ nodes: [], edges: [] });
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [forecast, setForecast] = useState<TrendForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    Promise.all([
      api.domains(),
      api.skills(),
      api.behavior(),
      api.skillGraph(),
      api.anomalies(),
      api.patterns(),
      api.trendForecast(),
    ]).then(([i, s, b, g, a, p, f]) => {
      setDomains(i);
      setSkills(s);
      setBehavior(b);
      setGraph(g);
      setAnomalies(a);
      setPatterns(p);
      setForecast(f);
      setLoading(false);
    });
  }, [ready]);

  if (!ready) return null;

  return (
    <AppShell>
      <PageHeader title={t("insights.title")} />

      {loading ? (
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : (
        <>
          <Section title={t("insights.howEvolving")}>
            <DomainGroups domains={domains} />
          </Section>

          <Section title={t("insights.skills")}>
            {skills.length === 0 ? (
              <p className="text-sm text-muted">Not enough data yet.</p>
            ) : (
              skills.map((s) => (
                <div key={s.skill} className="flex justify-between py-1 text-sm">
                  <span className="text-ink">{s.skill}</span>
                  <span className="text-muted">{s.activity_score}/100</span>
                </div>
              ))
            )}
          </Section>

          <Section title={t("insights.skillGraph")}>
            {graph.edges.length === 0 ? (
              <p className="text-sm text-muted">No progression edges yet — as your skills connect (e.g. Python → Machine Learning), they'll show up here.</p>
            ) : (
              graph.edges.map((e, i) => (
                <div key={i} className="py-0.5 font-mono text-sm text-ink">
                  {e.from} → {e.to}
                </div>
              ))
            )}
          </Section>

          {behavior && (
            <Section title={t("insights.behavior")}>
              <div className="space-y-1 text-sm text-ink">
                <div>
                  Completion Rate: {(behavior.completion_rate * 100).toFixed(0)}% ({behavior.source})
                </div>
                <div>Deep Work: {behavior.deep_work_hours_per_day}h/day</div>
                <div>Context Switching: {behavior.context_switching_per_day}/day</div>
              </div>
            </Section>
          )}

          {forecast && (
            <Section title={t("insights.trendForecast")}>
              <ForecastRow label="Completion Rate" unit="" forecast={forecast.completion_rate} />
              <ForecastRow label="Deep Work" unit="h/day" forecast={forecast.deep_work_hours_per_day} />
            </Section>
          )}

          <Section title={t("insights.unusualActivity")}>
            {anomalies.length === 0 ? (
              <p className="text-sm text-muted">Nothing unusual this week.</p>
            ) : (
              anomalies.map((a) => (
                <div key={a.metric} className="mb-1.5 flex items-start justify-between text-sm text-ink">
                  <span>
                    <strong>{a.metric}</strong> is {a.ratio ? `${a.ratio.toFixed(1)}x` : ""} your 8-week average ({Math.round(a.current_value)} vs ~
                    {Math.round(a.baseline_mean)} min).
                  </span>
                  <ConfidenceBadge confidence={a.confidence} />
                </div>
              ))
            )}
          </Section>

          <Section title={t("insights.patterns")}>
            {patterns.length === 0 ? (
              <p className="text-sm text-muted">No strong associations detected yet.</p>
            ) : (
              patterns.map((p, i) => (
                <div key={i} className="mb-1.5 flex items-start justify-between text-sm text-ink">
                  <p>{p.description}</p>
                  <ConfidenceBadge confidence={p.confidence} />
                </div>
              ))
            )}
          </Section>
        </>
      )}
    </AppShell>
  );
}
