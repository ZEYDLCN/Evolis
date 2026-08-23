"use client";

import { useEffect, useState } from "react";
import NavBar from "../../components/NavBar";
import { useRequireAuth } from "../../lib/useAuth";
import { api } from "../../lib/api";
import { page, card, mutedText, pill } from "../../lib/styles";

export default function TimelinePage() {
  const ready = useRequireAuth();
  const [timeline, setTimeline] = useState<Record<string, string[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    api
      .timeline()
      .then(setTimeline)
      .finally(() => setLoading(false));
  }, [ready]);

  if (!ready) return null;

  const months = Object.keys(timeline).sort();

  return (
    <>
      <NavBar />
      <main style={page}>
        <h1>Timeline</h1>
        <p style={mutedText}>Topics you've touched, grouped by month.</p>

        {loading ? (
          <p style={mutedText}>Loading...</p>
        ) : months.length === 0 ? (
          <p style={mutedText}>No entries yet — log a few days on the Today page first.</p>
        ) : (
          months.map((month) => (
            <div key={month} style={card}>
              <strong>{month}</strong>
              <div style={{ marginTop: 10 }}>
                {timeline[month].map((topic) => (
                  <span key={topic} style={pill}>
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}
      </main>
    </>
  );
}
