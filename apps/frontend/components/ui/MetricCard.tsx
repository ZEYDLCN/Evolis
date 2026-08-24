import { ReactNode } from "react";
import { Card } from "./Card";

export function MetricCard({ label, value, footer }: { label: string; value: ReactNode; footer?: ReactNode }) {
  return (
    <Card>
      <div className="text-xs font-medium uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1.5 text-2xl font-semibold text-ink">{value}</div>
      {footer && <div className="mt-1 text-xs text-muted">{footer}</div>}
    </Card>
  );
}
