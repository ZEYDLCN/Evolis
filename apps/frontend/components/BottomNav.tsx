"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "../lib/cn";

const ITEMS = [
  { href: "/dashboard", label: "Home", icon: "🏠" },
  { href: "/today", label: "Today", icon: "✍️" },
  { href: "/evolution", label: "Evolution", icon: "📈" },
  { href: "/ask", label: "Ask", icon: "💬" },
  { href: "/profile", label: "Profile", icon: "👤" },
];

export default function BottomNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-x-0 bottom-0 z-10 flex border-t border-line bg-card md:hidden">
      {ITEMS.map((item) => {
        const active = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[11px] font-medium",
              active ? "text-brand-emerald" : "text-muted"
            )}
          >
            <span className="text-lg leading-none">{item.icon}</span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
