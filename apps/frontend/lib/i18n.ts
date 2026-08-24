export type Lang = "en" | "tr";

const LANG_KEY = "evolis_lang";

/** Static UI chrome only (nav, page headers, buttons, empty states).
 * Backend-generated prose (dashboard insight text, weekly review
 * highlights, Ask Evolis answers) stays in whatever language the user
 * wrote their entries in — translating that would need a backend i18n
 * pass, out of scope here. */
const DICT: Record<Lang, Record<string, string>> = {
  en: {
    "nav.overview": "Overview",
    "nav.today": "Today",
    "nav.timeline": "Timeline",
    "nav.evolution": "Evolution",
    "nav.projects": "Projects",
    "nav.goals": "Goals",
    "nav.focus": "Focus",
    "nav.insights": "Insights",
    "nav.ask": "Ask Evolis",
    "nav.profile": "Profile",
    "nav.logout": "Log out",
    "nav.search": "Search",

    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.add": "Add",
    "common.edit": "Edit",
    "common.delete": "Delete",
    "common.export": "Export",
    "common.loading": "Loading...",
    "common.viewMore": "View more",

    "theme.light": "Light mode",
    "theme.dark": "Dark mode",
    "lang.label": "Language",

    "today.title": "Today",
    "today.description": "Tell Evolis what you worked on, learned, completed, or struggled with.",
    "today.saveEntry": "Save entry",
    "today.recentEntries": "Recent entries",

    "timeline.title": "Timeline",

    "evolution.title": "Evolution",
    "evolution.description": "Your version history, compared side by side.",
    "evolution.tab.current": "Current Version",
    "evolution.tab.history": "Version History",
    "evolution.tab.compare": "Compare Versions",
    "evolution.tab.releaseNotes": "Release Notes",

    "projects.title": "Projects",
    "projects.description": "Projects are auto-linked when an entry mentions them, or add one directly.",

    "goals.title": "Goals",
    "goals.description": "Rule-based suggestions from your own data — you decide what becomes a real goal.",
    "goals.suggested": "Suggested for you",
    "goals.active": "Active",
    "goals.completed": "Completed",
    "goals.addAsGoal": "Add as goal",
    "goals.markDone": "Mark done",
    "goals.remove": "Remove",

    "focus.title": "Focus",
    "focus.description": "Run a timed session — completed minutes count toward your deep work.",
    "focus.today": "Today",
    "focus.sessionsLogged": "Sessions logged",
    "focus.recentSessions": "Recent sessions",
    "focus.start": "Start",
    "focus.pause": "Pause",
    "focus.endAndLog": "End & log",

    "insights.title": "Insights",
    "insights.howEvolving": "How You're Evolving",
    "insights.skills": "Skills",
    "insights.skillGraph": "Skill Graph",
    "insights.behavior": "Behavior",
    "insights.trendForecast": "Trend Forecast",
    "insights.unusualActivity": "Unusual Activity",
    "insights.patterns": "Patterns",

    "ask.title": "Ask Evolis",
    "ask.description": "Ask a question about your own history — every number in the answer is computed, not guessed.",
    "ask.placeholder": "How have I changed in the last 3 months?",
    "ask.send": "Ask",

    "settings.title": "Settings",
    "settings.description": "Account, appearance, and privacy.",
    "settings.account": "Account",
    "settings.appearance": "Appearance",
    "settings.privacy": "Privacy",
    "settings.exportData": "Export my data",
    "settings.deleteAccount": "Delete account",

    "landing.hero": "Version control for your life.",
    "landing.sub": "Evolis turns your daily notes into real analytics — skills, focus, habits, projects, and interests — so you can see how you've actually changed, not just remember that you did.",
    "landing.cta": "Start your first entry",
    "landing.login": "Log in",
    "landing.getStarted": "Get started",

    "login.login": "Log in",
    "login.register": "Register",
    "login.email": "Email",
    "login.password": "Password",
    "login.createAccount": "Create account",

    "empty.noData": "Not enough data yet.",
  },
  tr: {
    "nav.overview": "Genel Bakış",
    "nav.today": "Bugün",
    "nav.timeline": "Zaman Çizelgesi",
    "nav.evolution": "Gelişim",
    "nav.projects": "Projeler",
    "nav.goals": "Hedefler",
    "nav.focus": "Odak",
    "nav.insights": "İçgörüler",
    "nav.ask": "Evolis'e Sor",
    "nav.profile": "Profil",
    "nav.logout": "Çıkış Yap",
    "nav.search": "Ara",

    "common.save": "Kaydet",
    "common.cancel": "Vazgeç",
    "common.add": "Ekle",
    "common.edit": "Düzenle",
    "common.delete": "Sil",
    "common.export": "Dışa Aktar",
    "common.loading": "Yükleniyor...",
    "common.viewMore": "Daha fazla göster",

    "theme.light": "Açık Mod",
    "theme.dark": "Koyu Mod",
    "lang.label": "Dil",

    "today.title": "Bugün",
    "today.description": "Evolis'e ne üzerinde çalıştığını, ne öğrendiğini, neyi tamamladığını ya da nerede zorlandığını anlat.",
    "today.saveEntry": "Kaydet",
    "today.recentEntries": "Son Kayıtlar",

    "timeline.title": "Zaman Çizelgesi",

    "evolution.title": "Gelişim",
    "evolution.description": "Versiyon geçmişin, yan yana karşılaştırmalı.",
    "evolution.tab.current": "Mevcut Versiyon",
    "evolution.tab.history": "Versiyon Geçmişi",
    "evolution.tab.compare": "Versiyonları Karşılaştır",
    "evolution.tab.releaseNotes": "Sürüm Notları",

    "projects.title": "Projeler",
    "projects.description": "Bir kayıtta bahsedilen projeler otomatik bağlanır, ya da doğrudan ekleyebilirsin.",

    "goals.title": "Hedefler",
    "goals.description": "Kendi verilerinden kural tabanlı öneriler — neyin gerçek bir hedefe dönüşeceğine sen karar verirsin.",
    "goals.suggested": "Sana Özel Öneriler",
    "goals.active": "Aktif",
    "goals.completed": "Tamamlanan",
    "goals.addAsGoal": "Hedef Olarak Ekle",
    "goals.markDone": "Tamamlandı Olarak İşaretle",
    "goals.remove": "Kaldır",

    "focus.title": "Odak",
    "focus.description": "Zamanlanmış bir seans başlat — tamamlanan dakikalar derin çalışma sürene eklenir.",
    "focus.today": "Bugün",
    "focus.sessionsLogged": "Kaydedilen Seans",
    "focus.recentSessions": "Son Seanslar",
    "focus.start": "Başlat",
    "focus.pause": "Duraklat",
    "focus.endAndLog": "Bitir ve Kaydet",

    "insights.title": "İçgörüler",
    "insights.howEvolving": "Nasıl Gelişiyorsun",
    "insights.skills": "Beceriler",
    "insights.skillGraph": "Beceri Grafiği",
    "insights.behavior": "Davranış",
    "insights.trendForecast": "Eğilim Tahmini",
    "insights.unusualActivity": "Olağan Dışı Aktivite",
    "insights.patterns": "Örüntüler",

    "ask.title": "Evolis'e Sor",
    "ask.description": "Kendi geçmişin hakkında bir soru sor — cevaptaki her sayı hesaplanır, tahmin edilmez.",
    "ask.placeholder": "Son 3 ayda nasıl değiştim?",
    "ask.send": "Sor",

    "settings.title": "Ayarlar",
    "settings.description": "Hesap, görünüm ve gizlilik.",
    "settings.account": "Hesap",
    "settings.appearance": "Görünüm",
    "settings.privacy": "Gizlilik",
    "settings.exportData": "Verilerimi Dışa Aktar",
    "settings.deleteAccount": "Hesabı Sil",

    "landing.hero": "Hayatın için versiyon kontrolü.",
    "landing.sub": "Evolis günlük notlarını gerçek analitiğe dönüştürür — beceriler, odak, alışkanlıklar, projeler ve ilgi alanların — böylece gerçekten nasıl değiştiğini görebilirsin, sadece değiştiğini hatırlamak yerine.",
    "landing.cta": "İlk kaydını oluştur",
    "landing.login": "Giriş Yap",
    "landing.getStarted": "Başla",

    "login.login": "Giriş Yap",
    "login.register": "Kayıt Ol",
    "login.email": "E-posta",
    "login.password": "Şifre",
    "login.createAccount": "Hesap Oluştur",

    "empty.noData": "Henüz yeterli veri yok.",
  },
};

export function getLang(): Lang {
  if (typeof window === "undefined") return "en";
  const stored = window.localStorage.getItem(LANG_KEY);
  return stored === "tr" ? "tr" : "en";
}

export function setLangStorage(lang: Lang) {
  try {
    window.localStorage.setItem(LANG_KEY, lang);
  } catch {
    // ignore (private browsing, storage disabled)
  }
}

export function translate(lang: Lang, key: string): string {
  return DICT[lang][key] ?? DICT.en[key] ?? key;
}
