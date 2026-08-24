"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { clearToken } from "../lib/api";
import { cn } from "../lib/cn";
import EvolisLogo from "./EvolisLogo";
import ThemeToggle from "./ThemeToggle";
import NotificationBell from "./NotificationBell";
import { useLang } from "./LangProvider";

const NAV_ITEMS = [
  { href: "/dashboard", key: "nav.overview" },
  { href: "/today", key: "nav.today" },
  { href: "/timeline", key: "nav.timeline" },
  { href: "/evolution", key: "nav.evolution" },
  { href: "/projects", key: "nav.projects" },
  { href: "/goals", key: "nav.goals" },
  { href: "/focus", key: "nav.focus" },
  { href: "/insights", key: "nav.insights" },
  { href: "/ask", key: "nav.ask" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { t } = useLang();

  return (
    <aside className="fixed inset-y-0 left-0 hidden w-60 flex-col border-r border-line bg-card px-4 py-6 md:flex">
      <Link href="/dashboard" className="mb-8 px-2">
        <EvolisLogo size={28} />
      </Link>

      <div className="mb-4 flex items-center gap-2">
        <button
          onClick={() => window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", metaKey: true }))}
          className="flex flex-1 items-center justify-between rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
        >
          <span>{t("nav.search")}</span>
          <kbd className="rounded border border-line bg-card px-1.5 py-0.5 text-[10px] font-medium">⌘K</kbd>
        </button>
        <NotificationBell />
      </div>

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
              {t(item.key)}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-1 border-t border-line pt-3">
        <ThemeToggle className="mb-1 flex items-center justify-between rounded-xl px-3 py-2 text-sm font-medium text-muted transition-colors hover:bg-surface hover:text-ink" />
        <Link
          href="/profile"
          className={cn(
            "rounded-xl px-3 py-2 text-sm font-medium transition-colors",
            pathname === "/profile" ? "bg-brand-emerald/10 text-brand-emerald" : "text-muted hover:bg-surface hover:text-ink"
          )}
        >
          {t("nav.profile")}
        </Link>
        <button
          onClick={() => {
            clearToken();
            router.push("/login");
          }}
          className="rounded-xl px-3 py-2 text-left text-sm font-medium text-muted transition-colors hover:bg-surface hover:text-ink"
        >
          {t("nav.logout")}
        </button>
      </div>
    </aside>
  );
}
