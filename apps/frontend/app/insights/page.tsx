"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Anomaly, Behavior, Pattern, SkillNode, TrendForecastResponse } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { CardSkeleton } from "../../components/ui/Skeleton";

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

export default function InsightsPage() {
  const ready = useRequireAuth();
  const [interests, setInterests] = useState<Record<string, number>>({});
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
      api.interests(),
      api.skills(),
      api.behavior(),
      api.skillGraph(),
      api.anomalies(),
      api.patterns(),
      api.trendForecast(),
    ]).then(([i, s, b, g, a, p, f]) => {
      setInterests(i);
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
      <PageHeader title="Insights" />

      {loading ? (
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : (
        <>
          <Section title="Interest Drift">
            {Object.keys(interests).length === 0 ? (
              <p className="text-sm text-muted">Not enough data yet.</p>
            ) : (
              Object.entries(interests).map(([topic, score]) => <Bar key={topic} label={topic} value={score} />)
            )}
          </Section>

          <Section title="Skills">
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

          <Section title="Skill Graph">
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
            <Section title="Behavior">
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
            <Section title="Trend Forecast">
              <ForecastRow label="Completion Rate" unit="" forecast={forecast.completion_rate} />
              <ForecastRow label="Deep Work" unit="h/day" forecast={forecast.deep_work_hours_per_day} />
            </Section>
          )}

          <Section title="Unusual Activity">
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

          <Section title="Patterns">
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
