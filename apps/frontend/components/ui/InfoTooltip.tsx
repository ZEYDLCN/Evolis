"use client";

import { useState } from "react";

/** "Explain This Metric" (section 55): a tiny hover/tap affordance next to
 * a metric label that explains, in plain language, what it measures and
 * how it's computed — so a number never has to be taken on faith. */
export function InfoTooltip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-block">
      <button
        type="button"
        aria-label="What does this mean?"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={() => setOpen((o) => !o)}
        className="ml-1 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border border-line text-[9px] font-bold leading-none text-muted hover:border-brand-emerald hover:text-brand-emerald"
      >
        i
      </button>
      {open && (
        <span className="absolute bottom-full left-1/2 z-20 mb-1.5 w-48 -translate-x-1/2 rounded-lg border border-line bg-card p-2 text-[11px] font-normal normal-case leading-snug text-ink shadow-lg">
          {text}
        </span>
      )}
    </span>
  );
}
