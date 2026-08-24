"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, DashboardSummary } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";
import { InsightCard } from "../../components/ui/InsightCard";
import { DeltaBadge } from "../../components/ui/Badge";
import { Button } from "../../components/ui/Button";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const ready = useRequireAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    api
      .dashboardSummary()
      .then(setSummary)
      .finally(() => setLoading(false));
  }, [ready]);

  if (!ready) return null;

  return (
    <AppShell>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-ink">
          {greeting()}
          {summary?.greeting_name ? `, ${summary.greeting_name}.` : "."}
        </h1>
      </div>

      {loading ? (
        <div className="space-y-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : !summary ? (
        <EmptyState title="Couldn't load your dashboard" description="Try refreshing the page." />
      ) : summary.onboarding_gate ? (
        <EmptyState
          icon="🌱"
          title={summary.hero_headline}
          description="Evolis needs a handful of entries before it has something real to say."
          action={
            <Link href="/today">
              <Button>Log today's entry</Button>
            </Link>
          }
        />
      ) : (
        <div className="space-y-6">
          <Card className="border-brand-emerald/15">
            <p className="text-lg font-medium text-ink">{summary.hero_headline}</p>
            {summary.hero_stats.length > 0 && (
              <ul className="mt-3 space-y-1">
                {summary.hero_stats.map((stat, i) => (
                  <li key={i} className="text-sm text-muted">
                    · {stat}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          {summary.current_version && (
            <Card>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="font-mono text-lg font-semibold text-ink">YOU v{summary.current_version.label}</div>
                  <div className="text-xs text-muted">
                    {summary.current_version.period_start} → {summary.current_version.period_end}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Link href="/evolution">
                    <Button variant="secondary">View Version</Button>
                  </Link>
                  {summary.current_version.has_previous_version && (
                    <Link href="/evolution?tab=compare">
                      <Button variant="secondary">Compare</Button>
                    </Link>
                  )}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                <div>
                  <div className="text-xs uppercase tracking-wide text-muted">Primary Focus</div>
                  <div className="mt-1 text-sm font-semibold text-ink">{summary.current_version.primary_focus ?? "—"}</div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-muted">Strongest Growth</div>
                  <div className="mt-1 text-sm font-semibold text-ink">
                    {summary.current_version.strongest_growth
                      ? `${summary.current_version.strongest_growth.topic} +${Math.round(summary.current_version.strongest_growth.change * 100)}%`
                      : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-muted">Completion</div>
                  <div className="mt-1 text-sm font-semibold text-ink">
                    {summary.current_version.completion_rate !== null ? `${Math.round(summary.current_version.completion_rate * 100)}%` : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase tracking-wide text-muted">Deep Work</div>
                  <div className="mt-1 text-sm font-semibold text-ink">
                    {summary.current_version.deep_work_hours_per_day !== null ? `${summary.current_version.deep_work_hours_per_day}h/day` : "—"}
                  </div>
                </div>
              </div>
            </Card>
          )}

          {summary.focus_shift.length > 0 && (
            <Card>
              <div className="mb-3 text-sm font-semibold text-ink">Focus Shift — Last 90 Days</div>
              <div className="space-y-2.5">
                {summary.focus_shift.map((row) => (
                  <div key={row.topic} className="flex items-center gap-3">
                    <div className="w-32 shrink-0 truncate text-sm text-ink">{row.topic}</div>
                    <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-surface">
                      <div className="h-full rounded-full bg-brand-emerald" style={{ width: `${Math.min(100, row.score * 100)}%` }} />
                    </div>
                    <div className="w-10 shrink-0 text-right text-xs text-muted">{Math.round(row.score * 100)}</div>
                  </div>
                ))}
              </div>
              {summary.focus_shift_note && <p className="mt-3 text-sm text-muted">{summary.focus_shift_note}</p>}
            </Card>
          )}

          <Card>
            <div className="mb-3 text-sm font-semibold text-ink">This Week vs Last Week</div>
            <div className="space-y-2">
              {summary.weekly_evolution.map((row) => (
                <div key={row.key} className="flex items-center justify-between py-1">
                  <span className="text-sm text-ink">{row.label}</span>
                  <DeltaBadge changePct={row.change} isPositive={row.is_positive} />
                </div>
              ))}
            </div>
          </Card>

          {summary.insight && (
            <InsightCard
              headline={summary.insight.headline}
              detail={summary.insight.detail}
              action={
                <Link href="/ask" className="text-sm font-semibold text-brand-emerald hover:underline">
                  Ask Evolis about this →
                </Link>
              }
            />
          )}

          {summary.recent_activity.length > 0 && (
            <Card>
              <div className="mb-3 text-sm font-semibold text-ink">Recent Activity</div>
              <div className="space-y-3">
                {summary.recent_activity.map((a, i) => (
                  <div key={i} className="flex items-baseline gap-3">
                    <div className="w-24 shrink-0 text-xs font-medium text-muted">{a.when}</div>
                    <div className="text-sm text-ink">{a.summary}</div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}
    </AppShell>
  );
}
