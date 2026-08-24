"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api, SearchResults } from "../lib/api";
import { getToken } from "../lib/api";

/** Global Cmd+K / Ctrl+K search across entries, projects, topics, skills,
 * and versions (section 14). Purely a navigation shortcut — no LLM, no
 * ranking beyond what src/services/search_service.py already returns. */
export default function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
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
        .search(q)
        .then(setResults)
        .finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(handle);
  }, [query, open]);

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
          placeholder="Search entries, projects, topics, skills..."
          className="w-full rounded-t-2xl border-b border-line bg-transparent px-4 py-3.5 text-sm text-ink placeholder:text-muted focus:outline-none"
        />
        <div className="max-h-96 overflow-y-auto p-2">
          {!query.trim() && <div className="px-2 py-4 text-center text-xs text-muted">Type to search, Esc to close.</div>}
          {loading && <div className="px-2 py-4 text-center text-xs text-muted">Searching...</div>}
          {results && !loading && !hasResults && query.trim() && (
            <div className="px-2 py-4 text-center text-xs text-muted">No results for "{query}"</div>
          )}

          {results && results.projects.length > 0 && (
            <Section title="Projects">
              {results.projects.map((p) => (
                <Row key={p.id} onClick={() => go(`/projects/${p.id}`)}>
                  📁 {p.name}
                </Row>
              ))}
            </Section>
          )}

          {results && results.entries.length > 0 && (
            <Section title="Entries">
              {results.entries.map((e) => (
                <Row key={e.id} onClick={() => go(`/day/${e.date}`)}>
                  <span className="text-muted">{e.date}</span> — {e.snippet}
                </Row>
              ))}
            </Section>
          )}

          {results && results.topics.length > 0 && (
            <Section title="Topics">
              {results.topics.map((t) => (
                <Row key={t} onClick={() => go(`/timeline`)}>
                  🏷️ {t}
                </Row>
              ))}
            </Section>
          )}

          {results && results.skills.length > 0 && (
            <Section title="Skills">
              {results.skills.map((s) => (
                <Row key={s.id} onClick={() => go(`/insights`)}>
                  🧠 {s.name}
                </Row>
              ))}
            </Section>
          )}

          {results && results.versions.length > 0 && (
            <Section title="Versions">
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
