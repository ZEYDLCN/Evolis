import { HTMLAttributes } from "react";
import { cn } from "../../lib/cn";

type Tone = "neutral" | "positive" | "negative" | "info";

const tones: Record<Tone, string> = {
  neutral: "bg-surface text-ink border border-line",
  positive: "bg-brand-lime/30 text-brand-forest",
  negative: "bg-red-50 text-red-700",
  info: "bg-brand-emerald/10 text-brand-emerald",
};

export function Badge({ tone = "neutral", className, ...props }: HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn("inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium", tones[tone], className)}
      {...props}
    />
  );
}

/** Polarity-aware delta badge: the spec's own example is a metric that
 * improves by going *down* (context switching), so "good" is a caller
 * decision (isPositive), never inferred from the sign of the number. */
export function DeltaBadge({ changePct, isPositive }: { changePct: number | null; isPositive: boolean | null }) {
  if (changePct === null) return <Badge tone="neutral">—</Badge>;
  const sign = changePct >= 0 ? "+" : "";
  const tone: Tone = isPositive === null ? "neutral" : isPositive ? "positive" : "negative";
  return <Badge tone={tone}>{`${sign}${(changePct * 100).toFixed(0)}%`}</Badge>;
}
