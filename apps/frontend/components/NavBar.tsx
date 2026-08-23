"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken } from "../lib/api";

const LINKS = [
  { href: "/today", label: "Today" },
  { href: "/timeline", label: "Timeline" },
  { href: "/diff", label: "Diff" },
  { href: "/profile", label: "Profile" },
  { href: "/projects", label: "Projects" },
  { href: "/insights", label: "Insights" },
  { href: "/ask", label: "Ask LifeDiff" },
];

export default function NavBar() {
  const router = useRouter();

  return (
    <header style={{ borderBottom: "1px solid #eee", marginBottom: "2rem" }}>
      <div
        style={{
          maxWidth: 900,
          margin: "0 auto",
          padding: "1rem 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <Link href="/" style={{ fontWeight: 700, textDecoration: "none", color: "#111" }}>
          LifeDiff
        </Link>
        <nav style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} style={{ fontSize: 14, color: "#444", textDecoration: "none" }}>
              {l.label}
            </Link>
          ))}
          <button
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
            style={{ fontSize: 14, background: "none", border: "none", color: "#999", cursor: "pointer" }}
          >
            Log out
          </button>
        </nav>
      </div>
    </header>
  );
}
