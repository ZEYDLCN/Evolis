"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, WeeklyReview } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { PageHeader } from "../../components/ui/PageHeader";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { EmptyState } from "../../components/ui/EmptyState";

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <div className="text-2xl font-semibold text-ink">{value}</div>
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
    </div>
  );
}

export default function WeeklyReviewPage() {
  const ready = useRequireAuth();
  const [review, setReview] = useState<WeeklyReview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    api
      .weeklyReview()
      .then(setReview)
      .finally(() => setLoading(false));
  }, [ready]);

  if (!ready) return null;

  return (
    <AppShell>
      <PageHeader title="Your Week in Evolis" description={review ? `${review.period_start} → ${review.period_end}` : undefined} />

      {loading ? (
        <CardSkeleton />
      ) : !review ? (
        <EmptyState title="Couldn't load your weekly review" />
      ) : review.entries_count === 0 ? (
        <EmptyState icon="📅" title="No entries this week yet" description="Log a few days and your weekly review will show up here." />
      ) : (
        <div className="space-y-6">
          <Card>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label="Entries" value={review.entries_count} />
              <Stat label="Learning" value={`${review.learning_hours}h`} />
              <Stat label="Projects Touched" value={review.projects_touched} />
              <Stat label="Task Completion" value={`${Math.round(review.completion_rate * 100)}%`} />
            </div>
          </Card>

          <Card>
            <div className="text-xs uppercase tracking-wide text-muted">Top Focus</div>
            <div className="mt-1 text-lg font-semibold text-ink">{review.top_focus ?? "—"}</div>
          </Card>

          {review.emerging_topic && (
            <Card className="bg-brand-lime/10">
              <div className="text-xs uppercase tracking-wide text-brand-emerald">Emerging</div>
              <div className="mt-1 text-lg font-semibold text-ink">{review.emerging_topic}</div>
            </Card>
          )}

          {review.biggest_improvement && (
            <Card>
              <div className="text-xs uppercase tracking-wide text-muted">Biggest Improvement</div>
              <div className="mt-1 text-lg font-semibold text-ink">
                {review.biggest_improvement.label} {review.biggest_improvement.change >= 0 ? "+" : ""}
                {Math.round(review.biggest_improvement.change * 100)}%
              </div>
            </Card>
          )}

          {review.watch && (
            <Card className="border-amber-200 bg-amber-50">
              <div className="text-xs uppercase tracking-wide text-amber-700">Watch</div>
              <div className="mt-1 text-lg font-semibold text-ink">
                {review.watch.label} {review.watch.change >= 0 ? "+" : ""}
                {Math.round(review.watch.change * 100)}%
              </div>
            </Card>
          )}

          <Link href="/ask">
            <Button>Ask Evolis about my week</Button>
          </Link>
        </div>
      )}
    </AppShell>
  );
}
