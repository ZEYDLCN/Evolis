"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { clearToken } from "../lib/api";
import { brand } from "../lib/styles";
import EvolisLogo from "./EvolisLogo";

const LINKS = [
  { href: "/today", label: "Today" },
  { href: "/timeline", label: "Timeline" },
  { href: "/diff", label: "Diff" },
  { href: "/profile", label: "Profile" },
  { href: "/projects", label: "Projects" },
  { href: "/insights", label: "Insights" },
  { href: "/ask", label: "Ask Evolis" },
];

export default function NavBar() {
  const router = useRouter();

  return (
    <header style={{ borderBottom: `1px solid ${brand.borderTint}`, marginBottom: "2rem", background: "#ffffff" }}>
      <div
        style={{
          maxWidth: 900,
          margin: "0 auto",
          padding: "0.75rem 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <Link href="/" style={{ textDecoration: "none" }}>
          <EvolisLogo size={32} />
        </Link>
        <nav style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          {LINKS.map((l) => (
            <Link key={l.href} href={l.href} style={{ fontSize: 14, color: brand.deepForest, textDecoration: "none" }}>
              {l.label}
            </Link>
          ))}
          <button
            onClick={() => {
              clearToken();
              router.push("/login");
            }}
            style={{ fontSize: 14, background: "none", border: "none", color: brand.mutedGreen, cursor: "pointer" }}
          >
            Log out
          </button>
        </nav>
      </div>
    </header>
  );
}
