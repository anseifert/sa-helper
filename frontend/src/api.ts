const API = import.meta.env.VITE_API_URL || "";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export interface Task {
  id: number;
  title: string;
  task_type: string;
  badge_source: string;
  origin_url: string | null;
  company_name: string | null;
  due_at: string | null;
  created_at: string;
}

export interface TaskGroup {
  company_key: string;
  company_name: string;
  company_id: number | null;
  tasks: Task[];
}

export interface Contact {
  id: number;
  email: string;
  display_name: string | null;
  company_name: string | null;
  company_override: string | null;
  is_internal: boolean;
  title: string | null;
  notes: string | null;
}

export interface Recommendation {
  id: number;
  rec_type: string;
  title: string;
  body: string | null;
  rank_score: number;
}

export interface Dashboard {
  recommendations: Recommendation[];
  focus_today: Recommendation[];
  open_tasks_by_company: { company_name: string; count: number }[];
  aging_buckets: { label: string; count: number }[];
  untouched_accounts_30d: { company_name: string }[];
  sync_health: {
    connector: string;
    status: string;
    last_run: string | null;
    error_message: string | null;
  }[];
}

export interface Settings {
  google_connected: boolean;
  slack_configured: boolean;
  last_sync_at: string | null;
}

export const api = {
  dashboard: () => fetchJson<Dashboard>("/api/v1/dashboard"),
  tasks: () => fetchJson<TaskGroup[]>("/api/v1/tasks"),
  contacts: (q?: string, companyId?: number) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (companyId) params.set("company_id", String(companyId));
    const qs = params.toString();
    return fetchJson<Contact[]>(`/api/v1/contacts${qs ? `?${qs}` : ""}`);
  },
  companies: () => fetchJson<{ id: number; name: string }[]>("/api/v1/companies"),
  updateContact: (id: number, body: { company_override?: string }) =>
    fetchJson<Contact>(`/api/v1/contacts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  enrichContact: (id: number) =>
    fetchJson<Contact>(`/api/v1/contacts/${id}/enrich`, { method: "POST" }),
  sync: () => fetchJson<{ status: string }>("/api/v1/sync", { method: "POST" }),
  settings: () => fetchJson<Settings>("/api/v1/settings"),
  health: () => fetchJson<{ status: string; google_connected: boolean }>("/api/v1/health"),
};

export function googleAuthUrl(): string {
  return `${API}/api/v1/oauth/google/authorize`;
}
