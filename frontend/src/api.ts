const API = import.meta.env.VITE_API_URL || "";

export interface AuthStatus {
  authenticated: boolean;
  username: string | null;
  login_configured?: boolean;
}

async function parseError(res: Response): Promise<string> {
  const text = await res.text();
  try {
    const data = JSON.parse(text) as { detail?: string | { msg?: string }[] };
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) {
      return data.detail.map((d) => d.msg ?? String(d)).join("; ");
    }
    return text || res.statusText;
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
  if (!res.ok) {
    const msg = await parseError(res);
    throw new Error(`${res.status} ${path}: ${msg}`);
  }
  return res.json();
}

export interface Task {
  id: number;
  status?: string;
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
  is_ignored?: boolean;
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

export interface TaskExclusions {
  emails: string[];
  companies: string[];
}

export interface TodayMeeting {
  event_id: string;
  title: string;
  start_at: string;
  end_at: string | null;
  external_emails: string[];
  html_link: string | null;
}

export interface Dashboard {
  recommendations: Recommendation[];
  focus_today: Recommendation[];
  today_meetings: TodayMeeting[];
  today_meetings_error?: string | null;
  open_tasks_by_company: {
    company_id: number | null;
    company_name: string;
    section_id: string;
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
    records_upserted?: number;
    error_message: string | null;
  }[];
  task_exclusions: TaskExclusions;
}

export interface AssetsCatalog {
  subscriptions: { key: string; label: string }[];
  hardware: { key: string; label: string }[];
}

export interface AssetCompany {
  company_id: number;
  company_name: string;
  company_domain: string;
  subscriptions: Record<string, boolean>;
  hardware: Record<string, boolean>;
  ansible_nodes: number;
  rhel_subscriptions: number;
}

export interface AvailableCompany {
  id: number;
  name: string;
  domain: string;
}

export type AssetCompanyPatch = Partial<{
  company_name: string;
  subscriptions: Record<string, boolean>;
  hardware: Record<string, boolean>;
  ansible_nodes: number;
  rhel_subscriptions: number;
}>;

export interface OnboardingStatus {
  google_connected: boolean;
  last_sync_at: string | null;
  onboarding_complete: boolean;
}

export interface Settings {
  google_connected: boolean;
  slack_configured: boolean;
  last_sync_at: string | null;
  user_email?: string | null;
  onboarding_complete: boolean;
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
  onboardingStatus: () => fetchJson<OnboardingStatus>("/api/v1/onboarding/status"),
  dashboard: () => fetchJson<Dashboard>("/api/v1/dashboard"),
  todayMeetings: () =>
    fetchJson<{ meetings: TodayMeeting[]; error: string | null }>(
      "/api/v1/dashboard/today-meetings"
    ),
  dismissRecommendation: (recId: number) =>
    fetchJson<Recommendation>(`/api/v1/recommendations/${recId}/dismiss`, {
      method: "POST",
    }),
  updateTaskExclusions: (body: TaskExclusions) =>
    fetchJson<TaskExclusions>("/api/v1/dashboard/exclusions", {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  tasks: () => fetchJson<TaskGroup[]>("/api/v1/tasks"),
  tasksSummary: () => fetchJson<TasksSummary>("/api/v1/tasks/summary"),
  completeTask: (taskId: number) =>
    fetchJson<Task>(`/api/v1/tasks/${taskId}/complete`, { method: "POST" }),
  contacts: (q?: string, companyId?: number, includeIgnored?: boolean) => {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (companyId) params.set("company_id", String(companyId));
    if (includeIgnored) params.set("include_ignored", "true");
    const qs = params.toString();
    return fetchJson<Contact[]>(`/api/v1/contacts${qs ? `?${qs}` : ""}`);
  },
  companies: () => fetchJson<{ id: number; name: string }[]>("/api/v1/companies"),
  assetsReady: () =>
    fetchJson<{ ready: boolean; error?: string; company_assets_rows?: number }>(
      "/api/v1/assets/ready"
    ),
  assetsCatalog: () => fetchJson<AssetsCatalog>("/api/v1/assets/catalog"),
  assets: () => fetchJson<AssetCompany[]>("/api/v1/assets"),
  assetsAvailableCompanies: () =>
    fetchJson<AvailableCompany[]>("/api/v1/assets/available-companies"),
  attachAssetCompany: (companyId: number) =>
    fetchJson<AssetCompany>("/api/v1/assets/companies", {
      method: "POST",
      body: JSON.stringify({ company_id: companyId }),
    }),
  updateAssetCompany: (companyId: number, body: AssetCompanyPatch) =>
    fetchJson<AssetCompany>(`/api/v1/assets/companies/${companyId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  updateContact: (
    id: number,
    body: { company_override?: string; is_ignored?: boolean }
  ) =>
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
