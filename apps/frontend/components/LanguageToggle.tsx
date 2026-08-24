"use client";

import { useLang } from "./LangProvider";

export default function LanguageToggle({ className }: { className?: string }) {
  const { lang, setLang, t } = useLang();

  return (
    <button
      onClick={() => setLang(lang === "en" ? "tr" : "en")}
      className={
        className ??
        "flex items-center justify-between rounded-xl border border-line bg-surface px-3 py-2 text-sm text-muted transition-colors hover:border-brand-emerald hover:text-brand-emerald"
      }
    >
      <span>{t("lang.label")}</span>
      <span className="font-mono text-xs font-semibold uppercase">{lang}</span>
    </button>
  );
}
