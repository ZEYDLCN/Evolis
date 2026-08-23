"use client";

import { useEffect, useState } from "react";
import NavBar from "../../components/NavBar";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Project } from "../../lib/api";
import { page, card, input, button, mutedText } from "../../lib/styles";

export default function ProjectsPage() {
  const ready = useRequireAuth();
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
    <>
      <NavBar />
      <main style={page}>
        <h1>Projects</h1>
        <p style={mutedText}>Projects are auto-linked when an entry mentions them, or add one directly.</p>

        <form onSubmit={submit} style={{ ...card, display: "flex", gap: 12 }}>
          <input style={input} placeholder="Project name" value={name} onChange={(e) => setName(e.target.value)} />
          <button type="submit" style={button} disabled={submitting || !name.trim()}>
            Add
          </button>
        </form>

        {loading ? (
          <p style={mutedText}>Loading...</p>
        ) : projects.length === 0 ? (
          <p style={mutedText}>No projects yet.</p>
        ) : (
          projects.map((p) => (
            <div key={p.id} style={card}>
              <strong>{p.name}</strong>
              {p.description && <p style={mutedText}>{p.description}</p>}
              {p.technologies && p.technologies.length > 0 && <p style={mutedText}>{p.technologies.join(", ")}</p>}
            </div>
          ))
        )}
      </main>
    </>
  );
}
