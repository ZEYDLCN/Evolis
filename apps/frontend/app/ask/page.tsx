"use client";

import { useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, AskEvidence, ApiError, ToolTraceStep } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";
import { useLang } from "../../components/LangProvider";
import { cn } from "../../lib/cn";

const SUGGESTION_KEYS = ["ask.suggestion1", "ask.suggestion2", "ask.suggestion3", "ask.suggestion4", "ask.suggestion5"];

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  queryClass?: string;
  evidence?: AskEvidence;
  toolTrace?: ToolTraceStep[];
}

/** Tool Transparency (section 45): shows the actual steps the LangGraph
 * pipeline ran, in plain language — never a black box even though the
 * final wording is LLM-generated. */
function ToolTracePanel({ trace }: { trace: ToolTraceStep[] }) {
  const [expanded, setExpanded] = useState(false);
  const { t } = useLang();
  if (trace.length === 0) return null;

  return (
    <div className="mt-2 border-t border-line pt-2">
      <button onClick={() => setExpanded((e) => !e)} className="text-xs font-semibold text-muted hover:text-brand-emerald">
        {expanded ? t("ask.hide") : t("ask.howComputed")}
      </button>
      {expanded && (
        <ol className="mt-2 space-y-1.5">
          {trace.map((step, i) => (
            <li key={i} className="text-xs text-muted">
              <span className="font-mono uppercase text-brand-emerald">{step.step}</span> — {step.detail}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function EvidencePanel({ evidence }: { evidence: AskEvidence }) {
  const [expanded, setExpanded] = useState(false);
  const { t } = useLang();
  if (evidence.entries_analyzed === 0 && evidence.bullets.length === 0) return null;

  return (
    <div className="mt-3 border-t border-line pt-3">
      <div className="text-xs font-medium text-muted">
        {t("ask.basedOn")} {evidence.entries_analyzed} {evidence.entries_analyzed === 1 ? t("ask.entry") : t("ask.entries")}
      </div>
      {evidence.bullets.length > 0 && (
        <ul className="mt-1.5 space-y-0.5">
          {evidence.bullets.map((b, i) => (
            <li key={i} className="text-xs text-muted">
              • {b}
            </li>
          ))}
        </ul>
      )}
      {evidence.source_entries.length > 0 && (
        <>
          <button onClick={() => setExpanded((e) => !e)} className="mt-2 text-xs font-semibold text-brand-emerald hover:underline">
            {expanded ? t("ask.hideEvidence") : t("ask.viewEvidence")}
          </button>
          {expanded && (
            <div className="mt-2 space-y-2">
              {evidence.source_entries.map((text, i) => (
                <div key={i} className="rounded-lg bg-surface p-2.5 text-xs text-ink">
                  {text}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function AskPage() {
  const ready = useRequireAuth();
  const { t } = useLang();
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask(q: string) {
    if (!q.trim() || loading) return;
    setError(null);
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);
    try {
      const result = await api.ask(q);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: result.answer, queryClass: result.query_class, evidence: result.evidence, toolTrace: result.tool_trace },
      ]);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to get an answer");
    } finally {
      setLoading(false);
    }
  }

  if (!ready) return null;

  return (
    <AppShell>
      <PageHeader title={t("ask.title")} description={t("ask.description")} />

      {messages.length === 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {SUGGESTION_KEYS.map((key) => (
            <button
              key={key}
              onClick={() => ask(t(key))}
              className="rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
            >
              {t(key)}
            </button>
          ))}
        </div>
      )}

      <div className="mb-4 space-y-4">
        {messages.map((m, i) =>
          m.role === "user" ? (
            <div key={i} className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-brand-emerald px-4 py-2.5 text-sm text-white">{m.text}</div>
            </div>
          ) : (
            <div key={i} className="flex justify-start">
              <Card className="max-w-[85%] rounded-bl-sm">
                {m.queryClass && (
                  <Badge tone="info" className="mb-2">
                    {t(`query.${m.queryClass}`)}
                  </Badge>
                )}
                <p className="text-sm text-ink">{m.text}</p>
                {m.evidence && <EvidencePanel evidence={m.evidence} />}
                {m.toolTrace && <ToolTracePanel trace={m.toolTrace} />}
              </Card>
            </div>
          )
        )}
        {loading && (
          <div className="flex justify-start">
            <Card className="rounded-bl-sm">
              <p className="text-sm text-muted">{t("ask.thinking")}</p>
            </Card>
          </div>
        )}
      </div>

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(question);
        }}
        className={cn("sticky bottom-4 flex gap-3 rounded-2xl border border-line bg-card p-2 shadow-sm", "md:bottom-6")}
      >
        <Input
          className="border-none focus:ring-0"
          placeholder={t("ask.placeholder")}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <Button type="submit" disabled={loading || !question.trim()}>
          {t("ask.send")}
        </Button>
      </form>
    </AppShell>
  );
}
