const API = import.meta.env.VITE_API_URL || "";

export interface AuthStatus {
  authenticated: boolean;
  username: string | null;
  login_configured?: boolean;
}

async function parseError(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const data = JSON.parse(text) as { detail?: string };
    return data.detail || text || res.statusText;
  } catch {
    return text || res.statusText;
  }
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    credentials: "include",
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (res.status === 401 && !path.startsWith("/api/v1/auth/")) {
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Not authenticated");
  }
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export interface Task {
  id: number;
  title: string;
  description?: string | null;
  task_type: string;
  badge_source: string;
  origin_url: string | null;
  company_name: string | null;
  due_at: string | null;
  created_at: string;
}

export interface AccountSummary {
  account_key: string;
  display_name: string;
  task_count: number;
  summary: string;
  tasks: Task[];
}

export interface TaskCategory {
  category: string;
  label: string;
  task_count: number;
  summary: string;
  tasks: Task[];
}

export interface TasksSummary {
  priority_accounts: AccountSummary[];
  concur: TaskCategory;
  redhat_direct: TaskCategory;
  other_accounts: AccountSummary[];
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
  open_tasks_by_company: {
    company_id: number | null;
    company_name: string;
    count: number;
  }[];
  aging_buckets: { label: string; count: number }[];
  untouched_accounts_30d: {
    company_id: number;
    company_name: string;
    last_touch: string | null;
  }[];
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

export interface SyncStatus {
  last_sync_at: string | null;
  in_progress: boolean;
  connectors: Record<
    string,
    { status: string; records_upserted: number; error: string | null }
  >;
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export const api = {
  authMe: () => fetchJson<AuthStatus>("/api/v1/auth/me"),
  login: (username: string, password: string) =>
    fetchJson<AuthStatus>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  logout: () =>
    fetchJson<AuthStatus>("/api/v1/auth/logout", { method: "POST" }),
  dashboard: () => fetchJson<Dashboard>("/api/v1/dashboard"),
  tasks: () => fetchJson<TaskGroup[]>("/api/v1/tasks"),
  tasksSummary: () => fetchJson<TasksSummary>("/api/v1/tasks/summary"),
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
  syncStart: () =>
    fetchJson<{ status: string; message: string }>("/api/v1/sync", { method: "POST" }),
  syncStatus: () => fetchJson<SyncStatus>("/api/v1/sync/status"),
  waitForSync: async (maxWaitMs = 600_000) => {
    const deadline = Date.now() + maxWaitMs;
    while (Date.now() < deadline) {
      const status = await fetchJson<SyncStatus>("/api/v1/sync/status");
      if (!status.in_progress) return status;
      await sleep(2000);
    }
    throw new Error("Sync is taking longer than expected. Check back in a few minutes.");
  },
  /** Start sync in background and poll until finished (avoids gateway timeouts). */
  sync: async () => {
    const start = await fetchJson<{ status: string; message: string }>("/api/v1/sync", {
      method: "POST",
    });
    const deadline = Date.now() + 600_000;
    while (Date.now() < deadline) {
      const status = await fetchJson<SyncStatus>("/api/v1/sync/status");
      if (!status.in_progress) return start;
      await sleep(2000);
    }
    throw new Error("Sync is taking longer than expected. Check back in a few minutes.");
  },
  settings: () => fetchJson<Settings>("/api/v1/settings"),
  health: () => fetchJson<{ status: string; google_connected: boolean }>("/api/v1/health"),
};

export function googleAuthUrl(): string {
  return `${API}/api/v1/oauth/google/authorize`;
}
