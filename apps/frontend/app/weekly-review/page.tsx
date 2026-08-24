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
import { useLang } from "../../components/LangProvider";

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
  const { t } = useLang();
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
      <PageHeader title={t("weekly.title")} description={review ? `${review.period_start} → ${review.period_end}` : undefined} />

      {loading ? (
        <CardSkeleton />
      ) : !review ? (
        <EmptyState title={t("weekly.couldntLoad")} />
      ) : review.entries_count === 0 ? (
        <EmptyState icon="📅" title={t("weekly.noEntries")} description={t("weekly.logFewDays")} />
      ) : (
        <div className="space-y-6">
          <Card>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <Stat label={t("weekly.entries")} value={review.entries_count} />
              <Stat label={t("weekly.learning")} value={`${review.learning_hours}h`} />
              <Stat label={t("weekly.projectsTouched")} value={review.projects_touched} />
              <Stat label={t("weekly.taskCompletion")} value={`${Math.round(review.completion_rate * 100)}%`} />
            </div>
          </Card>

          <Card>
            <div className="text-xs uppercase tracking-wide text-muted">{t("weekly.topFocus")}</div>
            <div className="mt-1 text-lg font-semibold text-ink">{review.top_focus ?? "—"}</div>
          </Card>

          {review.emerging_topic && (
            <Card className="bg-brand-lime/10">
              <div className="text-xs uppercase tracking-wide text-brand-emerald">{t("weekly.emerging")}</div>
              <div className="mt-1 text-lg font-semibold text-ink">{review.emerging_topic}</div>
            </Card>
          )}

          {review.biggest_improvement && (
            <Card>
              <div className="text-xs uppercase tracking-wide text-muted">{t("weekly.biggestImprovement")}</div>
              <div className="mt-1 text-lg font-semibold text-ink">
                {review.biggest_improvement.label} {review.biggest_improvement.change >= 0 ? "+" : ""}
                {Math.round(review.biggest_improvement.change * 100)}%
              </div>
            </Card>
          )}

          {review.watch && (
            <Card className="border-amber-200 bg-amber-50">
              <div className="text-xs uppercase tracking-wide text-amber-700">{t("weekly.watch")}</div>
              <div className="mt-1 text-lg font-semibold text-ink">
                {review.watch.label} {review.watch.change >= 0 ? "+" : ""}
                {Math.round(review.watch.change * 100)}%
              </div>
            </Card>
          )}

          <Link href="/ask">
            <Button>{t("weekly.askAboutWeek")}</Button>
          </Link>
        </div>
      )}
    </AppShell>
  );
}
