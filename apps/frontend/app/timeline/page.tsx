"use client";

import { useEffect, useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { EmptyState } from "../../components/ui/EmptyState";
import { CardSkeleton } from "../../components/ui/Skeleton";

export default function TimelinePage() {
  const ready = useRequireAuth();
  const [timeline, setTimeline] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    api
      .timeline()
      .then(setTimeline)
      .finally(() => setLoading(false));
  }, [ready]);

  if (!ready) return null;

  const months = Object.keys(timeline).sort();

  return (
    <AppShell>
      <PageHeader title="Timeline" description="Topics you've touched, grouped by month." />

      {loading ? (
        <div className="space-y-3">
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : months.length === 0 ? (
        <EmptyState icon="🗓️" title="No entries yet" description="Log a few days on the Today page first." />
      ) : (
        <div className="space-y-3">
          {months.map((month) => (
            <Card key={month}>
              <div className="mb-2 font-semibold text-ink">{month}</div>
              <div className="flex flex-wrap gap-1.5">
                {timeline[month].map((topic) => (
                  <Badge key={topic}>{topic}</Badge>
                ))}
              </div>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
