"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { getToken } from "../lib/api";
import EvolisLogo from "../components/EvolisLogo";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

const FEATURES = [
  { icon: "📝", title: "Daily entries, structured automatically", detail: "Write in plain language — Evolis extracts topics, activities, and status for you." },
  { icon: "📈", title: "Every score is computed, not guessed", detail: "Interests, skills, and behavior come from your own data — the LLM only phrases it." },
  { icon: "🔀", title: "See yourself over time", detail: "Versioned snapshots of who you were, with a real diff between any two points." },
  { icon: "💬", title: "Ask Evolis about your own history", detail: "Get grounded answers, backed by the entries that produced them." },
];

/** Landing Page (section 56): the public root. A returning user with a
 * token skips straight past this to /dashboard; a first-time visitor
 * gets a real marketing page instead of a redirect flash to /login. */
export default function Home() {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    if (getToken()) {
      router.replace("/dashboard");
    } else {
      setChecked(true);
    }
  }, [router]);

  if (!checked) return null;

  return (
    <main className="min-h-screen bg-surface">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-6">
        <EvolisLogo size={32} />
        <div className="flex gap-2">
          <Link href="/login">
            <Button variant="ghost">Log in</Button>
          </Link>
          <Link href="/login">
            <Button>Get started</Button>
          </Link>
        </div>
      </div>

      <section className="mx-auto max-w-3xl px-6 pb-16 pt-12 text-center">
        <h1 className="text-4xl font-bold leading-tight text-ink md:text-5xl">Version control for your life.</h1>
        <p className="mx-auto mt-4 max-w-xl text-lg text-muted">
          Evolis turns your daily notes into real analytics — interests, skills, and behavior — so you can see how you've
          actually changed, not just remember that you did.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link href="/login">
            <Button className="px-6 py-3 text-base">Start your first entry</Button>
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-6 pb-24 sm:grid-cols-2">
        {FEATURES.map((f) => (
          <Card key={f.title}>
            <div className="mb-2 text-2xl">{f.icon}</div>
            <div className="mb-1 font-semibold text-ink">{f.title}</div>
            <p className="text-sm text-muted">{f.detail}</p>
          </Card>
        ))}
      </section>

      <footer className="border-t border-line px-6 py-8 text-center text-xs text-muted">
        Evolis — Personal Evolution Intelligence
      </footer>
    </main>
  );
}
