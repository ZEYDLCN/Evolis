export function Progress({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-line">
      <div className="h-full rounded-full bg-brand-emerald transition-all" style={{ width: `${pct}%` }} />
    </div>
  );
}
