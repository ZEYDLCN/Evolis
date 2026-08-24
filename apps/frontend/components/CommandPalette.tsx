"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, SearchResults } from "../lib/api";
import { getToken } from "../lib/api";
import { useLang } from "./LangProvider";

/** Global Cmd+K / Ctrl+K search across entries, projects, topics, skills,
 * and versions (section 14). Purely a navigation shortcut — no LLM, no
 * ranking beyond what src/services/search_service.py already returns. */
const DAY_FILTER_KEYS: { key: string; days: number | undefined }[] = [
  { key: "palette.allTime", days: undefined },
  { key: "palette.days7", days: 7 },
  { key: "palette.days30", days: 30 },
];

export default function CommandPalette() {
  const router = useRouter();
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [days, setDays] = useState<number | undefined>(undefined);
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 10);
    } else {
      setQuery("");
      setResults(null);
    }
  }, [open]);

  useEffect(() => {
    if (!open || !getToken()) return;
    const q = query.trim();
    if (!q) {
      setResults(null);
      return;
    }
    setLoading(true);
    const handle = setTimeout(() => {
      api
        .search(q, { days })
        .then(setResults)
        .finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(handle);
  }, [query, open, days]);

  function go(path: string) {
    setOpen(false);
    router.push(path);
  }

  if (!open) return null;

  const hasResults =
    results && (results.entries.length || results.projects.length || results.topics.length || results.skills.length || results.versions.length);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-ink/40 px-4 pt-24" onClick={() => setOpen(false)}>
      <div className="w-full max-w-lg rounded-2xl border border-line bg-card shadow-xl" onClick={(e) => e.stopPropagation()}>
        <input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t("palette.searchPlaceholder")}
          className="w-full rounded-t-2xl border-b border-line bg-transparent px-4 py-3.5 text-sm text-ink placeholder:text-muted focus:outline-none"
        />
        <div className="flex gap-1.5 border-b border-line px-3 py-2">
          {DAY_FILTER_KEYS.map((f) => (
            <button
              key={f.key}
              onClick={() => setDays(f.days)}
              className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                days === f.days ? "bg-brand-emerald text-white" : "bg-surface text-muted hover:text-ink"
              }`}
            >
              {t(f.key)}
            </button>
          ))}
        </div>
        <div className="max-h-96 overflow-y-auto p-2">
          {!query.trim() && <div className="px-2 py-4 text-center text-xs text-muted">{t("palette.typeToSearch")}</div>}
          {loading && <div className="px-2 py-4 text-center text-xs text-muted">{t("palette.searching")}</div>}
          {results && !loading && !hasResults && query.trim() && (
            <div className="px-2 py-4 text-center text-xs text-muted">
              {t("palette.noResultsFor")} "{query}"
            </div>
          )}

          {results && results.projects.length > 0 && (
            <Section title={t("palette.projects")}>
              {results.projects.map((p) => (
                <Row key={p.id} onClick={() => go(`/projects/${p.id}`)}>
                  📁 {p.name}
                </Row>
              ))}
            </Section>
          )}

          {results && results.entries.length > 0 && (
            <Section title={t("palette.entries")}>
              {results.entries.map((e) => (
                <Row key={e.id} onClick={() => go(`/day/${e.date}`)}>
                  <span className="text-muted">{e.date}</span> — {e.snippet}
                </Row>
              ))}
            </Section>
          )}

          {results && results.topics.length > 0 && (
            <Section title={t("palette.topics")}>
              {results.topics.map((topic) => (
                <Row key={topic} onClick={() => go(`/timeline`)}>
                  🏷️ {topic}
                </Row>
              ))}
            </Section>
          )}

          {results && results.skills.length > 0 && (
            <Section title={t("palette.skills")}>
              {results.skills.map((s) => (
                <Row key={s.id} onClick={() => go(`/insights`)}>
                  🧠 {s.name}
                </Row>
              ))}
            </Section>
          )}

          {results && results.versions.length > 0 && (
            <Section title={t("palette.versions")}>
              {results.versions.map((v) => (
                <Row key={v.id} onClick={() => go(`/evolution?tab=history`)}>
                  🏷️ {v.label}
                </Row>
              ))}
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-1">
      <div className="px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-muted">{title}</div>
      {children}
    </div>
  );
}

function Row({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="block w-full truncate rounded-lg px-2.5 py-2 text-left text-sm text-ink transition-colors hover:bg-surface"
    >
      {children}
    </button>
  );
}
