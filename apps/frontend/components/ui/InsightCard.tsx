import { ReactNode } from "react";
import { Card } from "./Card";

export function InsightCard({ eyebrow = "Evolis Insight", headline, detail, action }: { eyebrow?: string; headline: string; detail?: string | null; action?: ReactNode }) {
  return (
    <Card className="border-brand-emerald/20 bg-gradient-to-br from-brand-lime/10 to-card">
      <div className="text-xs font-semibold uppercase tracking-wide text-brand-emerald">{eyebrow}</div>
      <div className="mt-2 text-base font-medium text-ink">{headline}</div>
      {detail && <p className="mt-1 text-sm text-muted">{detail}</p>}
      {action && <div className="mt-3">{action}</div>}
    </Card>
  );
}
