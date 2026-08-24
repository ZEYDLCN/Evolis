"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AppShell from "../../../components/AppShell";
import { useRequireAuth } from "../../../lib/useAuth";
import { api, ProjectDetail } from "../../../lib/api";
import { Card } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { MetricCard } from "../../../components/ui/MetricCard";
import { PageHeader } from "../../../components/ui/PageHeader";
import { EmptyState } from "../../../components/ui/EmptyState";

export default function ProjectDetailPage() {
  const ready = useRequireAuth();
  const params = useParams<{ id: string }>();
  const [detail, setDetail] = useState<ProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    api
      .projectDetail(params.id)
      .then(setDetail)
      .catch(() => setError("Project not found."))
      .finally(() => setLoading(false));
  }, [ready, params.id]);

  if (!ready) return null;

  const maxHours = detail ? Math.max(1, ...detail.focus_trend.map((f) => f.hours)) : 1;

  return (
    <AppShell>
      {loading ? (
        <p className="text-sm text-muted">Loading...</p>
      ) : error || !detail ? (
        <EmptyState icon="📁" title="Project not found" />
      ) : (
        <>
          <PageHeader title={detail.name} description={detail.description || "Auto-tracked from your daily entries."} />

          {detail.technologies.length > 0 && (
            <div className="-mt-4 mb-6 flex flex-wrap gap-1.5">
              {detail.technologies.map((t) => (
                <Badge key={t}>{t}</Badge>
              ))}
            </div>
          )}

          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-3">
            <MetricCard label="Active Days" value={detail.active_days} />
            <MetricCard label="Sessions" value={detail.total_sessions} />
            <MetricCard label="Focus Hours" value={`${detail.estimated_focus_hours}h`} />
          </div>

          {detail.topics_touched.length > 0 && (
            <Card className="mb-6">
              <div className="mb-2 text-sm font-semibold text-ink">Topics touched</div>
              <div className="flex flex-wrap gap-1.5">
                {detail.topics_touched.map((t) => (
                  <Badge key={t} tone="info">
                    {t}
                  </Badge>
                ))}
              </div>
            </Card>
          )}

          {detail.focus_trend.length > 0 && (
            <Card className="mb-6">
              <div className="mb-3 text-sm font-semibold text-ink">Focus trend</div>
              <div className="flex items-end gap-2" style={{ height: 80 }}>
                {detail.focus_trend.map((f) => (
                  <div key={f.week} className="flex flex-1 flex-col items-center gap-1">
                    <div
                      className="w-full rounded-t-md bg-brand-emerald/70"
                      style={{ height: `${Math.max(4, (f.hours / maxHours) * 64)}px` }}
                      title={`${f.week}: ${f.hours}h`}
                    />
                    <span className="text-[9px] text-muted">{f.week.split("-W")[1]}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <div className="mb-3 text-sm font-semibold text-ink">Timeline</div>
          {detail.timeline.length === 0 ? (
            <EmptyState icon="🗓️" title="No entries yet" description="Mention this project in a daily entry to see it here." />
          ) : (
            <div className="space-y-3">
              {detail.timeline.map((row) => (
                <Link key={row.entry_id} href={`/day/${row.date}`}>
                  <Card className="transition-colors hover:border-brand-emerald/40">
                    <div className="mb-1.5 flex items-center justify-between">
                      <span className="text-xs text-muted">{row.date}</span>
                      {row.duration_minutes !== null && (
                        <span className="text-xs font-medium text-brand-emerald">{row.duration_minutes}min</span>
                      )}
                    </div>
                    <p className="text-sm text-ink">{row.snippet}</p>
                    {row.topic && <Badge className="mt-2">{row.topic}</Badge>}
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </>
      )}
    </AppShell>
  );
}
