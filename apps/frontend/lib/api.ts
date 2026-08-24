const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "evolis_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function fetchSvg(path: string): Promise<string> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { headers });
  if (!res.ok) throw new ApiError(res.status, res.statusText);
  return res.text();
}

export const api = {
  register: (email: string, password: string) =>
    apiFetch<{ access_token: string }>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) =>
    apiFetch<{ access_token: string }>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  googleConfig: () => apiFetch<{ enabled: boolean; client_id: string | null }>("/auth/google/config"),
  loginWithGoogle: (credential: string) =>
    apiFetch<{ access_token: string }>("/auth/google", { method: "POST", body: JSON.stringify({ credential }) }),

  addEntry: (text: string) => apiFetch<Entry>("/entries", { method: "POST", body: JSON.stringify({ text }) }),
  listEntries: () => apiFetch<Entry[]>("/entries"),

  streak: () => apiFetch<Streak>("/analytics/streak"),
  heatmap: (days = 365) => apiFetch<HeatmapDay[]>(`/analytics/heatmap?days=${days}`),
  onboarding: () => apiFetch<OnboardingStatus>("/analytics/onboarding"),
  dashboardSummary: () => apiFetch<DashboardSummary>("/dashboard/summary"),
  evolisScore: () => apiFetch<EvolisScore>("/analytics/evolis-score"),
  weeklyReview: () => apiFetch<WeeklyReview>("/analytics/weekly-review"),

  timeline: () => apiFetch<Record<string, string[]>>("/timeline"),

  interests: (months = 6) => apiFetch<Record<string, number>>(`/analytics/interests?months=${months}`),
  skills: (months = 6) => apiFetch<SkillNode[]>(`/analytics/skills?months=${months}`),
  behavior: (months = 3) => apiFetch<Behavior>(`/analytics/behavior?months=${months}`),
  skillGraph: (months = 6) => apiFetch<{ nodes: SkillNode[]; edges: { from: string; to: string }[] }>(`/analytics/skill-graph?months=${months}`),
  anomalies: () => apiFetch<Anomaly[]>("/analytics/anomalies"),
  patterns: () => apiFetch<Pattern[]>("/analytics/patterns"),

  listProjects: () => apiFetch<Project[]>("/projects"),
  createProject: (name: string) => apiFetch<Project>("/projects", { method: "POST", body: JSON.stringify({ name }) }),

  listVersions: () => apiFetch<Version[]>("/versions"),
  generateVersion: (period_start: string, period_end: string) =>
    apiFetch("/versions/generate", { method: "POST", body: JSON.stringify({ period_start, period_end }) }),

  diff: (base: string, target: string) => apiFetch<DiffResult>(`/diff?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`),
  releaseNotes: (base: string, target: string) =>
    apiFetch<{ text: string }>(`/release-notes?base=${encodeURIComponent(base)}&target=${encodeURIComponent(target)}`),

  exportData: () => apiFetch<Record<string, unknown>>("/me/export"),
  deleteAccount: () => apiFetch<void>("/me", { method: "DELETE" }),

  ask: (question: string) => apiFetch<AskResult>("/ask", { method: "POST", body: JSON.stringify({ question }) }),
};

export interface EntryInsight {
  streak: { current: number; longest: number; is_new_best: boolean };
  recurring_topics: { topic: string; mentions_this_week: number }[];
  new_topics: string[];
}

export interface Entry {
  id: string;
  raw_text: string;
  entry_date: string;
  completion_status: string | null;
  blockers: string[] | null;
  extraction: Record<string, unknown> | null;
  insight?: EntryInsight | null;
}

export interface Streak {
  current_streak: number;
  longest_streak: number;
  last_entry_date: string | null;
  is_new_best: boolean;
}

export interface HeatmapDay {
  date: string;
  count: number;
}

export interface OnboardingStep {
  key: string;
  label: string;
  done: boolean;
  progress: number;
  target: number;
}

export interface OnboardingStatus {
  all_done: boolean;
  steps: OnboardingStep[];
}

export interface SkillNode {
  skill: string;
  activity_score: number;
  first_seen: string;
  last_seen: string;
  project_usage: number;
  learning_sessions: number;
}

export interface Behavior {
  created: number;
  completed: number;
  completion_rate: number;
  source: string;
  context_switching_per_day: number;
  deep_work_hours_per_day: number;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  technologies: string[] | null;
}

export interface Version {
  id: string;
  label: string;
  period_start: string;
  period_end: string;
}

export interface DiffResult {
  base: string;
  target: string;
  added_topics: string[];
  declining_topics: string[];
  dormant_topics: string[];
  emerging_topics: string[];
  topic_score_changes: Record<string, number>;
  skill_changes: Record<string, { before: number; after: number; change: number }>;
  completion_change: number | null;
  deep_work_change: number | null;
  context_switching_change: number | null;
  completion_before: number | null;
  completion_after: number | null;
  deep_work_before: number | null;
  deep_work_after: number | null;
  context_switching_before: number | null;
  context_switching_after: number | null;
}

export interface Anomaly {
  metric: string;
  current_value: number;
  baseline_mean: number;
  z_score: number;
  ratio: number | null;
}

export interface Pattern {
  correlation: number;
  weeks_observed: number;
  description: string;
}

export interface DashboardVersionCard {
  label: string;
  period_start: string;
  period_end: string;
  primary_focus: string | null;
  strongest_growth: { topic: string; change: number } | null;
  completion_rate: number | null;
  deep_work_hours_per_day: number | null;
  has_previous_version: boolean;
  previous_label: string | null;
}

export interface DashboardWeeklyRow {
  key: string;
  label: string;
  before: number;
  after: number;
  change: number | null;
  is_positive: boolean | null;
}

export interface DashboardInsight {
  type: string;
  headline: string;
  detail: string | null;
}

export interface DashboardActivity {
  when: string;
  date: string;
  summary: string;
}

export interface DashboardSummary {
  greeting_name: string | null;
  hero_headline: string;
  hero_stats: string[];
  current_version: DashboardVersionCard | null;
  focus_shift: { topic: string; score: number }[];
  focus_shift_note: string | null;
  weekly_evolution: DashboardWeeklyRow[];
  insight: DashboardInsight | null;
  recent_activity: DashboardActivity[];
  streak: { current: number; longest: number };
  evolis_score: EvolisScore | null;
  onboarding_gate: boolean;
}

export interface AskEvidence {
  entries_analyzed: number;
  bullets: string[];
  source_entries: string[];
}

export interface AskResult {
  question: string;
  query_class: string;
  answer: string;
  grounded: boolean;
  analysis: Record<string, unknown>;
  evidence: AskEvidence;
}

export interface EvolisScore {
  consistency: number;
  focus: number;
  execution: number;
  learning: number;
}

export interface WeeklyReview {
  period_start: string;
  period_end: string;
  entries_count: number;
  learning_hours: number;
  projects_touched: number;
  completion_rate: number;
  top_focus: string | null;
  emerging_topic: string | null;
  biggest_improvement: { label: string; change: number } | null;
  watch: { label: string; change: number } | null;
}
