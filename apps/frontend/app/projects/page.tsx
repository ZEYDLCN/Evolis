"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AppShell from "../../components/AppShell";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Project } from "../../lib/api";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { PageHeader } from "../../components/ui/PageHeader";
import { EmptyState } from "../../components/ui/EmptyState";
import { useLang } from "../../components/LangProvider";

export default function ProjectsPage() {
  const ready = useRequireAuth();
  const { t } = useLang();
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    try {
      setProjects(await api.listProjects());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (ready) load();
  }, [ready]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await api.createProject(name);
      setName("");
      await load();
    } finally {
      setSubmitting(false);
    }
  }

  if (!ready) return null;

  return (
    <AppShell>
      <PageHeader title={t("projects.title")} description={t("projects.description")} />

      <Card className="mb-6">
        <form onSubmit={submit} className="flex gap-3">
          <Input placeholder="Project name" value={name} onChange={(e) => setName(e.target.value)} />
          <Button type="submit" disabled={submitting || !name.trim()}>
            {t("common.add")}
          </Button>
        </form>
      </Card>

      {loading ? null : projects.length === 0 ? (
        <EmptyState icon="📁" title="No projects yet" />
      ) : (
        <div className="space-y-3">
          {projects.map((p) => (
            <Link key={p.id} href={`/projects/${p.id}`}>
              <Card className="transition-colors hover:border-brand-emerald/40">
                <div className="font-semibold text-ink">{p.name}</div>
                {p.description && <p className="mt-1 text-sm text-muted">{p.description}</p>}
                {p.technologies && p.technologies.length > 0 && <p className="mt-1 text-sm text-muted">{p.technologies.join(", ")}</p>}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </AppShell>
  );
}
