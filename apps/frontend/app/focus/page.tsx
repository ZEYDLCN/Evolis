"use client";

import { useEffect, useRef, useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, FocusSession } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { PageHeader } from "../../components/ui/PageHeader";
import { EmptyState } from "../../components/ui/EmptyState";
import { useLang } from "../../components/LangProvider";

const DURATIONS = [25, 50, 90];

function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60)
    .toString()
    .padStart(2, "0");
  const s = (seconds % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}

/** Focus Sessions / Timer (section 26): a client-side Pomodoro-style timer.
 * The server only ever records a completed session (POST /focus-sessions)
 * — there's no server-side timer state to keep in sync, and the logged
 * minutes feed straight into deep_work_hours_per_day like any other
 * FocusSession row. */
export default function FocusPage() {
  const ready = useRequireAuth();
  const { t } = useLang();
  const [durationMinutes, setDurationMinutes] = useState(25);
  const [remaining, setRemaining] = useState(25 * 60);
  const [running, setRunning] = useState(false);
  const [sessions, setSessions] = useState<FocusSession[]>([]);
  const [todayMinutes, setTodayMinutes] = useState(0);
  const [loading, setLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function load() {
    setLoading(true);
    try {
      const { sessions, today_minutes } = await api.focusSessions();
      setSessions(sessions);
      setTodayMinutes(today_minutes);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  useEffect(() => {
    if (!running) return;
    intervalRef.current = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          finish();
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [running]);

  function pickDuration(minutes: number) {
    if (running) return;
    setDurationMinutes(minutes);
    setRemaining(minutes * 60);
  }

  function start() {
    setRunning(true);
  }

  function pause() {
    setRunning(false);
  }

  async function finish() {
    setRunning(false);
    const elapsedSeconds = durationMinutes * 60 - remaining;
    const elapsedMinutes = Math.round(elapsedSeconds / 60);
    if (elapsedMinutes > 0) {
      await api.logFocusSession({ duration_minutes: elapsedMinutes });
      await load();
    }
    setRemaining(durationMinutes * 60);
  }

  if (!ready) return null;

  const progress = 1 - remaining / (durationMinutes * 60);

  return (
    <AppShell>
      <PageHeader title={t("focus.title")} description={t("focus.description")} />

      <Card className="mb-6 flex flex-col items-center py-10">
        <div className="mb-6 flex gap-2">
          {DURATIONS.map((d) => (
            <button
              key={d}
              onClick={() => pickDuration(d)}
              disabled={running}
              className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                durationMinutes === d ? "bg-brand-emerald text-white" : "bg-surface text-muted hover:text-ink"
              } disabled:opacity-50`}
            >
              {d}m
            </button>
          ))}
        </div>

        <div className="relative mb-6 flex h-48 w-48 items-center justify-center rounded-full border-4 border-line">
          <div
            className="absolute inset-0 rounded-full border-4 border-brand-emerald"
            style={{ clipPath: `inset(0 ${100 - progress * 100}% 0 0)` }}
          />
          <span className="font-mono text-4xl font-semibold text-ink">{formatClock(remaining)}</span>
        </div>

        <div className="flex gap-3">
          {!running ? (
            <Button onClick={start}>{remaining === durationMinutes * 60 ? t("focus.start") : "Resume"}</Button>
          ) : (
            <Button variant="secondary" onClick={pause}>
              {t("focus.pause")}
            </Button>
          )}
          {(running || remaining !== durationMinutes * 60) && (
            <Button variant="ghost" onClick={finish}>
              {t("focus.endAndLog")}
            </Button>
          )}
        </div>
      </Card>

      <div className="mb-6 grid grid-cols-2 gap-3">
        <Card>
          <div className="text-xs uppercase tracking-wide text-muted">{t("focus.today")}</div>
          <div className="mt-1 text-2xl font-semibold text-ink">{todayMinutes}min</div>
        </Card>
        <Card>
          <div className="text-xs uppercase tracking-wide text-muted">{t("focus.sessionsLogged")}</div>
          <div className="mt-1 text-2xl font-semibold text-ink">{sessions.length}</div>
        </Card>
      </div>

      <div className="mb-3 text-sm font-semibold text-ink">{t("focus.recentSessions")}</div>
      {loading ? (
        <p className="text-sm text-muted">{t("common.loading")}</p>
      ) : sessions.length === 0 ? (
        <EmptyState icon="⏱️" title="No sessions yet" description="Run your first timer above." />
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <Card key={s.id} className="flex items-center justify-between py-3">
              <span className="text-sm text-ink">{new Date(s.started_at).toLocaleString()}</span>
              <span className="text-sm font-medium text-brand-emerald">{s.duration_minutes}min</span>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
