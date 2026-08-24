"use client";

import { useEffect, useState } from "react";
import { api, Notification } from "../lib/api";
import { Badge } from "./ui/Badge";

const CONFIDENCE_TONE: Record<string, "positive" | "negative" | "neutral" | "info"> = {
  high: "info",
  medium: "neutral",
  low: "neutral",
};

/** Notification Center (section 33): derived, not stored — every item here
 * is re-computed from analytics that already exist (anomalies, patterns,
 * goal suggestions), so there's nothing to keep in sync and no read/unread
 * state to persist. See src/services/notification_service.py. */
export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[] | null>(null);

  useEffect(() => {
    api.notifications().then(setItems).catch(() => setItems([]));
  }, []);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-line bg-surface text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
      >
        🔔
        {items && items.length > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand-emerald text-[9px] font-bold text-white">
            {items.length}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute left-0 top-11 z-20 w-80 rounded-2xl border border-line bg-card p-2 shadow-lg">
            {!items || items.length === 0 ? (
              <div className="px-2 py-4 text-center text-xs text-muted">Nothing to flag right now.</div>
            ) : (
              items.map((n, i) => (
                <div key={i} className="rounded-xl px-2.5 py-2 hover:bg-surface">
                  <div className="mb-0.5 flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-ink">{n.title}</span>
                    <Badge tone={CONFIDENCE_TONE[n.confidence]} className="shrink-0 text-[10px]">
                      {n.confidence}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted">{n.detail}</p>
                </div>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
