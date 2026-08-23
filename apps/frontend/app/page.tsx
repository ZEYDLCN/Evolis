const SCREENS = ["Today", "Timeline", "Diff", "Profile", "Projects", "Insights", "Ask LifeDiff"];

export default function Home() {
  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "3rem 1.5rem" }}>
      <h1 style={{ marginBottom: 0 }}>LifeDiff</h1>
      <p style={{ color: "#666", marginTop: 4 }}>Version Control for Your Life</p>

      <nav style={{ display: "flex", gap: 12, flexWrap: "wrap", margin: "2rem 0" }}>
        {SCREENS.map((screen) => (
          <span
            key={screen}
            style={{
              border: "1px solid #ddd",
              borderRadius: 8,
              padding: "6px 12px",
              fontSize: 14,
            }}
          >
            {screen}
          </span>
        ))}
      </nav>

      <p style={{ color: "#888", fontSize: 14 }}>
        Frontend scaffold — screens wire up to the FastAPI backend at{" "}
        <code>NEXT_PUBLIC_API_URL</code>. See docs/ARCHITECTURE.md for the
        product spec and roadmap.
      </p>
    </main>
  );
}
