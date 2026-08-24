"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { getLang, Lang, setLangStorage, translate } from "../lib/i18n";

interface LangContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string) => string;
}

const LangContext = createContext<LangContextValue>({
  lang: "en",
  setLang: () => {},
  t: (key) => key,
});

/** Turkish UI mode: wraps the whole app so any component can call
 * useLang() to read/set the language and translate() static UI chrome
 * (nav, page headers, buttons). Starts "en" for a deterministic SSR
 * render, then syncs to localStorage on mount — a brief English flash
 * for a returning Turkish-mode user is an accepted trade-off here,
 * same as elsewhere in the app (see ThemeToggle). */
export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    setLangState(getLang());
  }, []);

  function setLang(next: Lang) {
    setLangState(next);
    setLangStorage(next);
  }

  return <LangContext.Provider value={{ lang, setLang, t: (key) => translate(lang, key) }}>{children}</LangContext.Provider>;
}

export function useLang() {
  return useContext(LangContext);
}
