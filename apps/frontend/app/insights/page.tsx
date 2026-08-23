"use client";

import { useEffect, useState } from "react";
import NavBar from "../../components/NavBar";
import { useRequireAuth } from "../../lib/useAuth";
import { api, Anomaly, Behavior, Pattern, SkillNode } from "../../lib/api";
import { page, card, mutedText } from "../../lib/styles";

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 14, marginBottom: 4 }}>
        <span>{label}</span>
        <span style={mutedText}>{(value * 100).toFixed(0)}%</span>
      </div>
      <div style={{ background: "#f0f0f0", borderRadius: 6, height: 8 }}>
        <div style={{ width: `${Math.min(value, 1) * 100}%`, background: "#111", borderRadius: 6, height: 8 }} />
      </div>
    </div>
  );
}

export default function InsightsPage() {
  const ready = useRequireAuth();
  const [interests, setInterests] = useState<Record<string, number>>({});
  const [skills, setSkills] = useState<SkillNode[]>([]);
  const [behavior, setBehavior] = useState<Behavior | null>(null);
  const [graph, setGraph] = useState<{ nodes: SkillNode[]; edges: { from: string; to: string }[] }>({ nodes: [], edges: [] });
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!ready) return;
    Promise.all([api.interests(), api.skills(), api.behavior(), api.skillGraph(), api.anomalies(), api.patterns()]).then(
      ([i, s, b, g, a, p]) => {
        setInterests(i);
        setSkills(s);
        setBehavior(b);
        setGraph(g);
        setAnomalies(a);
        setPatterns(p);
        setLoading(false);
      }
    );
  }, [ready]);

  if (!ready) return null;
  if (loading) return (<><NavBar /><main style={page}><p style={mutedText}>Loading...</p></main></>);

  return (
    <>
      <NavBar />
      <main style={page}>
        <h1>Insights</h1>

        <h2 style={{ fontSize: 18 }}>Interest Drift</h2>
        <div style={card}>
          {Object.keys(interests).length === 0 ? (
            <p style={mutedText}>Not enough data yet.</p>
          ) : (
            Object.entries(interests).map(([topic, score]) => <Bar key={topic} label={topic} value={score} />)
          )}
        </div>

        <h2 style={{ fontSize: 18 }}>Skills</h2>
        <div style={card}>
          {skills.length === 0 ? (
            <p style={mutedText}>Not enough data yet.</p>
          ) : (
            skills.map((s) => (
              <div key={s.skill} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0" }}>
                <span>{s.skill}</span>
                <span style={mutedText}>{s.activity_score}/100</span>
              </div>
            ))
          )}
        </div>

        <h2 style={{ fontSize: 18 }}>Skill Graph</h2>
        <div style={card}>
          {graph.edges.length === 0 ? (
            <p style={mutedText}>No progression edges yet — as your skills connect (e.g. Python → Machine Learning), they'll show up here.</p>
          ) : (
            graph.edges.map((e, i) => (
              <div key={i} style={{ fontFamily: "monospace", fontSize: 14, padding: "2px 0" }}>
                {e.from} → {e.to}
              </div>
            ))
          )}
        </div>

        <h2 style={{ fontSize: 18 }}>Behavior</h2>
        {behavior && (
          <div style={card}>
            <div>Completion Rate: {(behavior.completion_rate * 100).toFixed(0)}% ({behavior.source})</div>
            <div>Deep Work: {behavior.deep_work_hours_per_day}h/day</div>
            <div>Context Switching: {behavior.context_switching_per_day}/day</div>
          </div>
        )}

        <h2 style={{ fontSize: 18 }}>Unusual Activity</h2>
        <div style={card}>
          {anomalies.length === 0 ? (
            <p style={mutedText}>Nothing unusual this week.</p>
          ) : (
            anomalies.map((a) => (
              <div key={a.metric} style={{ marginBottom: 6 }}>
                <strong>{a.metric}</strong> is {a.ratio ? `${a.ratio.toFixed(1)}x` : ""} your 8-week average
                ({Math.round(a.current_value)} vs ~{Math.round(a.baseline_mean)} min).
              </div>
            ))
          )}
        </div>

        <h2 style={{ fontSize: 18 }}>Patterns</h2>
        <div style={card}>
          {patterns.length === 0 ? (
            <p style={mutedText}>No strong associations detected yet.</p>
          ) : (
            patterns.map((p, i) => <p key={i}>{p.description}</p>)
          )}
        </div>
      </main>
    </>
  );
}
