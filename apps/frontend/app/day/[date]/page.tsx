"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AppShell from "../../../components/AppShell";
import { useRequireAuth } from "../../../lib/useAuth";
import { api, DayDetail } from "../../../lib/api";
import { Card } from "../../../components/ui/Card";
import { Badge } from "../../../components/ui/Badge";
import { MetricCard } from "../../../components/ui/MetricCard";
import { PageHeader } from "../../../components/ui/PageHeader";
import { EmptyState } from "../../../components/ui/EmptyState";

const STATUS_TONE: Record<string, "positive" | "negative" | "neutral"> = {
  done: "positive",
  partial: "neutral",
  blocked: "negative",
  none: "neutral",
};

export default function DayDetailPage() {
  const ready = useRequireAuth();
  const params = useParams<{ date: string }>();
  const [detail, setDetail] = useState<DayDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    setLoading(true);
    api
      .dayDetail(params.date)
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [ready, params.date]);

  if (!ready) return null;

  const dateLabel = new Date(params.date + "T00:00:00").toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  return (
    <AppShell>
      <PageHeader title={dateLabel} description="Everything you logged on this day." />

      {loading ? (
        <p className="text-sm text-muted">Loading...</p>
      ) : !detail || detail.entry_count === 0 ? (
        <EmptyState icon="🗓️" title="No entries this day" />
      ) : (
        <>
          <div className="mb-6 grid grid-cols-2 gap-3 md:grid-cols-3">
            <MetricCard label="Entries" value={detail.entry_count} />
            <MetricCard label="Focused Minutes" value={detail.focused_minutes} />
            <MetricCard label="Topics" value={Object.keys(detail.topic_breakdown).length} />
          </div>

          {Object.keys(detail.topic_breakdown).length > 0 && (
            <Card className="mb-6">
              <div className="mb-2 text-sm font-semibold text-ink">Time by topic</div>
              <div className="space-y-2">
                {Object.entries(detail.topic_breakdown).map(([topic, minutes]) => (
                  <div key={topic} className="flex items-center justify-between text-sm">
                    <span className="text-ink">{topic}</span>
                    <span className="text-muted">{minutes}min</span>
                  </div>
                ))}
              </div>
            </Card>
          )}

          <div className="mb-3 text-sm font-semibold text-ink">Entries</div>
          <div className="space-y-3">
            {detail.entries.map((e) => (
              <Card key={e.id}>
                <div className="mb-2 flex items-center justify-between">
                  <Badge tone={STATUS_TONE[e.completion_status || "none"]}>{e.completion_status || "none"}</Badge>
                </div>
                <p className="text-sm text-ink">{e.text}</p>
                {e.topics.length > 0 && (
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {e.topics.map((t) => (
                      <Badge key={t}>{t}</Badge>
                    ))}
                  </div>
                )}
                {e.blockers.length > 0 && (
                  <div className="mt-2 text-xs text-red-600">Blocked: {e.blockers.join(", ")}</div>
                )}
              </Card>
            ))}
          </div>
        </>
      )}
    </AppShell>
  );
}
