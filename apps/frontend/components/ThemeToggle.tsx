"use client";

import { useEffect, useState } from "react";
import { getTheme, toggleTheme, Theme } from "../lib/theme";
import { useLang } from "./LangProvider";

export default function ThemeToggle({ className }: { className?: string }) {
  // Start "light" for a deterministic SSR render, then sync to whatever
  // the inline init script already applied — avoids a hydration mismatch
  // without needing a loading flash of its own.
  const [theme, setThemeState] = useState<Theme>("light");
  const { t } = useLang();

  useEffect(() => {
    setThemeState(getTheme());
  }, []);

  return (
    <button
      onClick={() => setThemeState(toggleTheme())}
      className={
        className ??
        "flex items-center justify-between rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
      }
    >
      <span>{theme === "dark" ? t("theme.dark") : t("theme.light")}</span>
      <span aria-hidden="true">{theme === "dark" ? "🌙" : "☀️"}</span>
    </button>
  );
}
