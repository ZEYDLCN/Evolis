"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "../lib/api";
import { cn } from "../lib/cn";
import EvolisLogo from "./EvolisLogo";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview" },
  { href: "/today", label: "Today" },
  { href: "/timeline", label: "Timeline" },
  { href: "/evolution", label: "Evolution" },
  { href: "/projects", label: "Projects" },
  { href: "/goals", label: "Goals" },
  { href: "/insights", label: "Insights" },
  { href: "/ask", label: "Ask Evolis" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="fixed inset-y-0 left-0 hidden w-60 flex-col border-r border-line bg-card px-4 py-6 md:flex">
      <Link href="/dashboard" className="mb-8 px-2">
        <EvolisLogo size={28} />
      </Link>

      <button
        onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
        className="mb-4 flex items-center justify-between rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
      >
        <span>Search</span>
        <kbd className="rounded border border-line bg-card px-1.5 py-0.5 text-[10px] font-medium">⌘K</kbd>
      </button>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-brand-emerald/10 text-brand-emerald" : "text-muted hover:bg-surface hover:text-ink"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-1 border-t border-line pt-3">
        <Link
          href="/profile"
          className={cn(
            "rounded-xl px-3 py-2 text-sm font-medium transition-colors",
            pathname === "/profile" ? "bg-brand-emerald/10 text-brand-emerald" : "text-muted hover:bg-surface hover:text-ink"
          )}
        >
          Profile
        </Link>
        <button
          onClick={() => {
            clearToken();
            router.push("/login");
          }}
          className="rounded-xl px-3 py-2 text-left text-sm font-medium text-muted transition-colors hover:bg-surface hover:text-ink"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}
