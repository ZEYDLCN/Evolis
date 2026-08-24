"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, fetchSvg, ApiError, DiffResult, Version } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input, Label } from "../../components/ui/Input";
import { Badge, DeltaBadge } from "../../components/ui/Badge";
import { Tabs } from "../../components/ui/Tabs";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";
import { useLang } from "../../components/LangProvider";

function isoMonthsAgo(months: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString().slice(0, 10);
}


export default function EvolutionPage() {
  return (
    <Suspense fallback={null}>
      <EvolutionPageInner />
    </Suspense>
  );
}

function EvolutionPageInner() {
  const ready = useRequireAuth();
  const { t } = useLang();
  const searchParams = useSearchParams();
  const VALID_TABS = ["current", "history", "compare", "release_notes"];
  const tabParam = searchParams.get("tab");
  const [tab, setTab] = useState(tabParam && VALID_TABS.includes(tabParam) ? tabParam : "current");
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (ready) api.listVersions().then(setVersions).finally(() => setLoading(false));
  }, [ready]);

  if (!ready) return null;

  const latest = versions[versions.length - 1];

  return (
    <AppShell>
      <PageHeader title={t("evolution.title")} description={t("evolution.description")} />

      <Tabs
        active={tab}
        onChange={setTab}
        tabs={[
          { key: "current", label: t("evolution.tab.current") },
          { key: "history", label: t("evolution.tab.history") },
          { key: "compare", label: t("evolution.tab.compare") },
          { key: "release_notes", label: t("evolution.tab.releaseNotes") },
        ]}
      />

      {loading ? null : tab === "current" ? (
        <CurrentVersionTab latest={latest} onGenerated={(v) => setVersions((prev) => [...prev, v])} />
      ) : tab === "history" ? (
        <VersionHistoryTab versions={versions} onGenerated={(v) => setVersions((prev) => [...prev, v])} />
      ) : tab === "compare" ? (
        <CompareTab versions={versions} />
      ) : (
        <ReleaseNotesTab versions={versions} />
      )}
    </AppShell>
  );
}

function GenerateVersionForm({ onGenerated }: { onGenerated: (v: Version) => void }) {
  const { t } = useLang();
  const [start, setStart] = useState(isoMonthsAgo(1));
  const [end, setEnd] = useState(new Date().toISOString().slice(0, 10));
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  async function generate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setGenerating(true);
    try {
      const result = await api.generateVersion(start, end);
      const versions = await api.listVersions();
      onGenerated(versions[versions.length - 1] ?? (result as unknown as Version));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("evolution.failedToGenerate"));
    } finally {
      setGenerating(false);
    }
  }

  return (
    <Card>
      <form onSubmit={generate} className="flex flex-wrap items-end gap-3">
        <div className="min-w-[140px] flex-1">
          <Label>{t("evolution.periodStart")}</Label>
          <Input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div className="min-w-[140px] flex-1">
          <Label>{t("evolution.periodEnd")}</Label>
          <Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <Button type="submit" disabled={generating}>
          {generating ? t("evolution.generating") : t("evolution.generateNew")}
        </Button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </Card>
  );
}

function CurrentVersionTab({ latest, onGenerated }: { latest: Version | undefined; onGenerated: (v: Version) => void }) {
  const { t } = useLang();
  if (!latest) {
    return (
      <div className="space-y-6">
        <EmptyState icon="📸" title={t("evolution.noVersionsYet")} description={t("evolution.generateFirst")} />
        <GenerateVersionForm onGenerated={onGenerated} />
      </div>
    );
  }
  return (
    <div className="space-y-6">
      <Card>
        <div className="font-mono text-xl font-semibold text-ink">YOU v{latest.label}</div>
        <div className="mt-1 text-sm text-muted">
          {latest.period_start} → {latest.period_end}
        </div>
      </Card>
      <GenerateVersionForm onGenerated={onGenerated} />
    </div>
  );
}

function monthLabel(iso: string): string {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, { month: "short", year: "numeric" });
}

function VersionHistoryTab({ versions, onGenerated }: { versions: Version[]; onGenerated: (v: Version) => void }) {
  const { t } = useLang();
  const [diffs, setDiffs] = useState<Record<string, DiffResult>>({});

  useEffect(() => {
    if (versions.length < 2) return;
    Promise.all(
      versions.slice(1).map(async (v, i) => {
        const prev = versions[i];
        try {
          return [v.label, await api.diff(prev.label, v.label)] as const;
        } catch {
          return null;
        }
      })
    ).then((results) => {
      const map: Record<string, DiffResult> = {};
      for (const r of results) {
        if (r) map[r[0]] = r[1];
      }
      setDiffs(map);
    });
  }, [versions]);

  return (
    <div className="space-y-6">
      <GenerateVersionForm onGenerated={onGenerated} />
      {versions.length === 0 ? (
        <EmptyState title={t("evolution.noVersionsYet")} description={t("evolution.generateOneAbove")} />
      ) : (
        <>
          {versions.length >= 2 && (
            <div className="overflow-x-auto pb-2">
              <div className="flex min-w-max items-center">
                {versions.map((v, i) => (
                  <div key={v.id} className="flex items-center">
                    {i > 0 && <div className="h-px w-12 bg-line" />}
                    <div className="flex flex-col items-center px-1">
                      <div className="h-2.5 w-2.5 rounded-full bg-brand-emerald" />
                      <div className="mt-1 font-mono text-xs font-semibold text-ink">v{v.label}</div>
                      <div className="text-[11px] text-muted">{monthLabel(v.period_start)}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-3">
            {[...versions].reverse().map((v) => {
              const d = diffs[v.label];
              return (
                <Card key={v.id}>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="font-mono font-semibold text-ink">YOU v{v.label}</div>
                      <div className="text-xs text-muted">{monthLabel(v.period_start)}</div>
                    </div>
                    <Link href={`/evolution?tab=compare`} className="text-sm font-semibold text-brand-emerald hover:underline">
                      {t("evolution.view")}
                    </Link>
                  </div>

                  {d && (
                    <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
                      {d.added_topics.length > 0 && (
                        <div>
                          <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{t("evolution.new")}</div>
                          <div className="flex flex-wrap gap-1.5">
                            {d.added_topics.slice(0, 4).map((topic) => (
                              <Badge key={topic} tone="positive">
                                + {topic}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {d.completion_change !== null && d.completion_change > 0 && (
                        <div>
                          <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">{t("evolution.improved")}</div>
                          <Badge tone="positive">
                            {t("evolution.completion")} +{Math.round(d.completion_change * 100)}%
                          </Badge>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function CompareTab({ versions }: { versions: Version[] }) {
  const { t } = useLang();
  const [base, setBase] = useState(versions[0]?.label ?? "");
  const [target, setTarget] = useState(versions[versions.length - 1]?.label ?? "");
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (versions.length >= 2) {
      setBase(versions[0].label);
      setTarget(versions[versions.length - 1].label);
    }
  }, [versions]);

  async function runDiff(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      setDiff(await api.diff(base, target));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t("evolution.failedToCompute"));
      setDiff(null);
    } finally {
      setLoading(false);
    }
  }

  if (versions.length < 2) {
    return <EmptyState icon="🔀" title={t("evolution.needTwoToCompare")} description={t("evolution.generateSecondInHistory")} />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <form onSubmit={runDiff} className="flex flex-wrap items-end gap-3">
          <div>
            <Label>{t("evolution.base")}</Label>
            <select
              className="rounded-xl border border-line bg-card px-3 py-2.5 text-sm"
              value={base}
              onChange={(e) => setBase(e.target.value)}
            >
              {versions.map((v) => (
                <option key={v.id} value={v.label}>
                  v{v.label}
                </option>
              ))}
            </select>
          </div>
          <span className="pb-2.5 text-muted">→</span>
          <div>
            <Label>{t("evolution.target")}</Label>
            <select
              className="rounded-xl border border-line bg-card px-3 py-2.5 text-sm"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
            >
              {versions.map((v) => (
                <option key={v.id} value={v.label}>
                  v{v.label}
                </option>
              ))}
            </select>
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? t("evolution.comparing") : t("evolution.compare")}
          </Button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </Card>

      {diff && (
        <div className="space-y-4">
          <div className="font-mono text-lg font-semibold text-ink">
            YOU v{diff.base} → YOU v{diff.target}
          </div>

          <DiffSection title={t("evolution.added")} tone="positive" prefix="+" topics={diff.added_topics} domainOf={diff.topic_domains} />
          <DiffSection title={t("evolution.emergingInterest")} tone="info" prefix="→" topics={diff.emerging_topics} domainOf={diff.topic_domains} />

          <Card>
            <div className="mb-3 text-sm font-semibold text-ink">{t("evolution.behavior")}</div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <BehaviorMetric label={t("evolution.deepWork")} before={diff.deep_work_before} after={diff.deep_work_after} unit="h" changePct={diff.deep_work_change} higherIsBetter />
              <BehaviorMetric
                label={t("evolution.completion")}
                before={diff.completion_before !== null ? diff.completion_before * 100 : null}
                after={diff.completion_after !== null ? diff.completion_after * 100 : null}
                unit="%"
                changePct={diff.completion_change}
                higherIsBetter
              />
              <BehaviorMetric
                label={t("evolution.contextSwitching")}
                before={diff.context_switching_before}
                after={diff.context_switching_after}
                unit="/day"
                changePct={
                  diff.context_switching_before && diff.context_switching_change !== null
                    ? diff.context_switching_change / diff.context_switching_before
                    : null
                }
                higherIsBetter={false}
              />
            </div>
          </Card>

          <DiffSection title={t("evolution.declining")} tone="negative" prefix="↓" topics={diff.declining_topics} domainOf={diff.topic_domains} />
          <DiffSection title={t("evolution.dormant")} tone="neutral" prefix="-" topics={diff.dormant_topics} domainOf={diff.topic_domains} />

          {Object.keys(diff.skill_changes).length > 0 && (
            <Card>
              <div className="mb-2 text-sm font-semibold text-ink">{t("evolution.skills")}</div>
              {Object.entries(diff.skill_changes).map(([skill, change]) => (
                <div key={skill} className="text-sm text-ink">
                  {skill}: {change.before} → {change.after} ({change.change >= 0 ? "+" : ""}
                  {change.change})
                </div>
              ))}
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

function BehaviorMetric({
  label,
  before,
  after,
  unit,
  changePct,
  higherIsBetter,
}: {
  label: string;
  before: number | null;
  after: number | null;
  unit: string;
  changePct: number | null;
  higherIsBetter: boolean;
}) {
  const isPositive = changePct === null || changePct === 0 ? null : (changePct > 0) === higherIsBetter;
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-muted">{label}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-lg font-semibold text-ink">
          {before !== null ? before.toFixed(1) : "—"}
          {unit}
        </span>
        <span className="text-muted">→</span>
        <span className="text-lg font-semibold text-ink">
          {after !== null ? after.toFixed(1) : "—"}
          {unit}
        </span>
      </div>
      <div className="mt-1.5">
        <DeltaBadge changePct={changePct} isPositive={isPositive} />
      </div>
    </div>
  );
}

/** Groups a diff section's topics by life domain (Skills, Work & Projects,
 * Learning, Habits & Routines, Personal Growth, Behavior) instead of one
 * flat badge list — Evolis tracks more than just tech skills, so a
 * version diff should read that way too. */
function DiffSection({
  title,
  tone,
  prefix,
  topics,
  domainOf,
}: {
  title: string;
  tone: "positive" | "negative" | "neutral" | "info";
  prefix: string;
  topics: string[];
  domainOf: Record<string, string>;
}) {
  const { t } = useLang();
  if (topics.length === 0) return null;

  const byDomain: Record<string, string[]> = {};
  for (const topic of topics) {
    const domain = domainOf[topic] ?? t("evolution.skills");
    (byDomain[domain] ??= []).push(topic);
  }

  return (
    <div>
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">{title}</div>
      <div className="space-y-2">
        {Object.entries(byDomain).map(([domain, domainTopics]) => (
          <div key={domain} className="flex flex-wrap items-center gap-2">
            <span className="text-[11px] font-medium text-muted">{domain}</span>
            {domainTopics.map((topic) => (
              <Badge key={topic} tone={tone}>
                {prefix} {topic}
              </Badge>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

function ReleaseNotesTab({ versions }: { versions: Version[] }) {
  const { t } = useLang();
  const [base, setBase] = useState(versions[0]?.label ?? "");
  const [target, setTarget] = useState(versions[versions.length - 1]?.label ?? "");
  const [text, setText] = useState<string | null>(null);
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    if (versions.length >= 2) {
      setBase(versions[0].label);
      setTarget(versions[versions.length - 1].label);
    }
  }, [versions]);

  async function loadNotes() {
    setText((await api.releaseNotes(base, target)).text);
  }

  async function loadCard() {
    setSvg(await fetchSvg(`/release-notes/card?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`));
  }

  function downloadCard() {
    if (!svg) return;
    const blob = new Blob([svg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `evolis-v${base}-v${target}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (versions.length < 2) {
    return <EmptyState icon="📝" title={t("evolution.needTwoForNotes")} description={t("evolution.generateSecondForNotes")} />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <Label>{t("evolution.base")}</Label>
            <select className="rounded-xl border border-line bg-card px-3 py-2.5 text-sm" value={base} onChange={(e) => setBase(e.target.value)}>
              {versions.map((v) => (
                <option key={v.id} value={v.label}>
                  v{v.label}
                </option>
              ))}
            </select>
          </div>
          <span className="pb-2.5 text-muted">→</span>
          <div>
            <Label>{t("evolution.target")}</Label>
            <select className="rounded-xl border border-line bg-card px-3 py-2.5 text-sm" value={target} onChange={(e) => setTarget(e.target.value)}>
              {versions.map((v) => (
                <option key={v.id} value={v.label}>
                  v{v.label}
                </option>
              ))}
            </select>
          </div>
          <Button variant="secondary" onClick={loadNotes} type="button">
            {t("evolution.loadReleaseNotes")}
          </Button>
          <Button variant="secondary" onClick={loadCard} type="button">
            {t("evolution.shareCard")}
          </Button>
        </div>
      </Card>

      {text && (
        <Card>
          <pre className="whitespace-pre-wrap font-mono text-sm text-ink">{text}</pre>
        </Card>
      )}

      {svg && (
        <Card>
          <div dangerouslySetInnerHTML={{ __html: svg }} />
          <Button className="mt-3" onClick={downloadCard}>
            {t("evolution.download")}
          </Button>
        </Card>
      )}
    </div>
  );
}
