"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, fetchSvg, ApiError, DiffResult, Version } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input, Label } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { Tabs } from "../../components/ui/Tabs";
import { EmptyState } from "../../components/ui/EmptyState";
import { PageHeader } from "../../components/ui/PageHeader";

function isoMonthsAgo(months: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - months);
  return d.toISOString().slice(0, 10);
}

function pct(x: number | null): string {
  if (x === null) return "—";
  const sign = x >= 0 ? "+" : "";
  return `${sign}${(x * 100).toFixed(0)}%`;
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
  const searchParams = useSearchParams();
  const [tab, setTab] = useState(searchParams.get("tab") === "compare" ? "compare" : "current");
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (ready) api.listVersions().then(setVersions).finally(() => setLoading(false));
  }, [ready]);

  if (!ready) return null;

  const latest = versions[versions.length - 1];

  return (
    <AppShell>
      <PageHeader title="Evolution" description="Your version history, compared side by side." />

      <Tabs
        active={tab}
        onChange={setTab}
        tabs={[
          { key: "current", label: "Current Version" },
          { key: "history", label: "Version History" },
          { key: "compare", label: "Compare Versions" },
          { key: "release_notes", label: "Release Notes" },
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
      setError(err instanceof ApiError ? err.message : "Failed to generate version");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <Card>
      <form onSubmit={generate} className="flex flex-wrap items-end gap-3">
        <div className="min-w-[140px] flex-1">
          <Label>Period start</Label>
          <Input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div className="min-w-[140px] flex-1">
          <Label>Period end</Label>
          <Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <Button type="submit" disabled={generating}>
          {generating ? "Generating..." : "Generate New Version"}
        </Button>
      </form>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </Card>
  );
}

function CurrentVersionTab({ latest, onGenerated }: { latest: Version | undefined; onGenerated: (v: Version) => void }) {
  if (!latest) {
    return (
      <div className="space-y-6">
        <EmptyState icon="📸" title="No versions yet" description="Generate your first version snapshot below." />
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

function VersionHistoryTab({ versions, onGenerated }: { versions: Version[]; onGenerated: (v: Version) => void }) {
  return (
    <div className="space-y-6">
      <GenerateVersionForm onGenerated={onGenerated} />
      {versions.length === 0 ? (
        <EmptyState title="No versions yet" description="Generate one above to start your version history." />
      ) : (
        <div className="space-y-2">
          {[...versions].reverse().map((v) => (
            <Card key={v.id} className="flex items-center justify-between py-3">
              <span className="font-mono font-semibold text-ink">YOU v{v.label}</span>
              <span className="text-sm text-muted">
                {v.period_start} → {v.period_end}
              </span>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function CompareTab({ versions }: { versions: Version[] }) {
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
      setError(err instanceof ApiError ? err.message : "Failed to compute diff");
      setDiff(null);
    } finally {
      setLoading(false);
    }
  }

  if (versions.length < 2) {
    return <EmptyState icon="🔀" title="Need two versions to compare" description="Generate a second version in Version History first." />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <form onSubmit={runDiff} className="flex flex-wrap items-end gap-3">
          <div>
            <Label>Base</Label>
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
            <Label>Target</Label>
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
            {loading ? "Comparing..." : "Compare"}
          </Button>
        </form>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
      </Card>

      {diff && (
        <div className="space-y-4">
          <div className="font-mono text-lg font-semibold text-ink">
            YOU v{diff.base} → YOU v{diff.target}
          </div>

          <DiffSection title="Added" tone="positive" items={diff.added_topics.map((t) => `+ ${t}`)} />
          <DiffSection title="Emerging Interest" tone="info" items={diff.emerging_topics.map((t) => `→ ${t}`)} />

          <Card>
            <div className="mb-2 text-sm font-semibold text-ink">Behavior</div>
            <div className="space-y-1 text-sm text-ink">
              <div>Completion Rate: {pct(diff.completion_change)}</div>
              <div>Deep Work: {pct(diff.deep_work_change)}</div>
              <div>Context Switching: {diff.context_switching_change ?? "—"}/day</div>
            </div>
          </Card>

          <DiffSection title="Declining" tone="negative" items={diff.declining_topics.map((t) => `↓ ${t}`)} />
          <DiffSection title="Dormant" tone="neutral" items={diff.dormant_topics.map((t) => `- ${t}`)} />

          {Object.keys(diff.skill_changes).length > 0 && (
            <Card>
              <div className="mb-2 text-sm font-semibold text-ink">Skills</div>
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

function DiffSection({ title, tone, items }: { title: string; tone: "positive" | "negative" | "neutral" | "info"; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">{title}</div>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <Badge key={item} tone={tone}>
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}

function ReleaseNotesTab({ versions }: { versions: Version[] }) {
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
    return <EmptyState icon="📝" title="Need two versions" description="Generate a second version to get release notes." />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <Label>Base</Label>
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
            <Label>Target</Label>
            <select className="rounded-xl border border-line bg-card px-3 py-2.5 text-sm" value={target} onChange={(e) => setTarget(e.target.value)}>
              {versions.map((v) => (
                <option key={v.id} value={v.label}>
                  v{v.label}
                </option>
              ))}
            </select>
          </div>
          <Button variant="secondary" onClick={loadNotes} type="button">
            Load Release Notes
          </Button>
          <Button variant="secondary" onClick={loadCard} type="button">
            Share Card
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
            Download
          </Button>
        </Card>
      )}
    </div>
  );
}
