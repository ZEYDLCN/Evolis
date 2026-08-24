"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Anomaly, Behavior, Pattern, SkillNode } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { PageHeader } from "../../components/ui/PageHeader";
import { CardSkeleton } from "../../components/ui/Skeleton";

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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    Promise.all([api.interests(), api.skills(), api.behavior(), api.skillGraph(), api.anomalies(), api.patterns()]).then(
      ([i, s, b, g, a, p]) => {
        setInterests(i);
        setSkills(s);
        setBehavior(b);
        setGraph(g);
        setAnomalies(a);
        setPatterns(p);
        setLoading(false);
      }
    );
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

          <Section title="Unusual Activity">
            {anomalies.length === 0 ? (
              <p className="text-sm text-muted">Nothing unusual this week.</p>
            ) : (
              anomalies.map((a) => (
                <div key={a.metric} className="mb-1.5 text-sm text-ink">
                  <strong>{a.metric}</strong> is {a.ratio ? `${a.ratio.toFixed(1)}x` : ""} your 8-week average ({Math.round(a.current_value)} vs ~
                  {Math.round(a.baseline_mean)} min).
                </div>
              ))
            )}
          </Section>

          <Section title="Patterns">
            {patterns.length === 0 ? (
              <p className="text-sm text-muted">No strong associations detected yet.</p>
            ) : (
              patterns.map((p, i) => (
                <p key={i} className="text-sm text-ink">
                  {p.description}
                </p>
              ))
            )}
          </Section>
        </>
      )}
    </AppShell>
  );
}
