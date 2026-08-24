"use client";

import { cn } from "../../lib/cn";

export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: { key: string; label: string }[];
  active: string;
  onChange: (key: string) => void;
}) {
  return (
    <div className="mb-6 flex gap-1 border-b border-line">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={cn(
            "border-b-2 px-3 py-2.5 text-sm font-medium transition-colors",
            active === tab.key ? "border-brand-emerald text-brand-emerald" : "border-transparent text-muted hover:text-ink"
          )}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
