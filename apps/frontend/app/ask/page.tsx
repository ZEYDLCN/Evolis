"use client";

import { useState } from "react";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, AskResult, ApiError } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Badge } from "../../components/ui/Badge";
import { PageHeader } from "../../components/ui/PageHeader";

const SUGGESTIONS = ["Son 6 ayda nasıl değiştim?", "Hangi konulara ilgim arttı?", "Son 3 ayda en fazla zaman ayırdığım teknik alan ne?"];

export default function AskPage() {
  const ready = useRequireAuth();
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function ask(q: string) {
    if (!q.trim()) return;
    setError(null);
    setLoading(true);
    setResult(null);
    try {
      setResult(await api.ask(q));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to get an answer");
    } finally {
      setLoading(false);
    }
  }

  if (!ready) return null;

  return (
    <AppShell>
      <PageHeader title="Ask Evolis" description="Ask a question about your own history — every number in the answer is computed, not guessed." />

      <Card className="mb-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            ask(question);
          }}
          className="flex gap-3"
        >
          <Input placeholder="Son 6 ayda nasıl değiştim?" value={question} onChange={(e) => setQuestion(e.target.value)} />
          <Button type="submit" disabled={loading || !question.trim()}>
            {loading ? "..." : "Ask"}
          </Button>
        </form>
      </Card>

      <div className="mb-6 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => {
              setQuestion(s);
              ask(s);
            }}
            className="rounded-full border border-line bg-surface px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
          >
            {s}
          </button>
        ))}
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {result && (
        <Card>
          <Badge tone="info" className="mb-3">
            {result.query_class}
          </Badge>
          <p className="text-base text-ink">{result.answer}</p>
          {result.grounded && <p className="mt-2 text-xs text-muted">✓ Grounded in your computed analytics</p>}
        </Card>
      )}
    </AppShell>
  );
}
