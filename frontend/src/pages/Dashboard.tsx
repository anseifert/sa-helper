import { useCallback, useEffect, useState } from "react";
import { api, Dashboard as Dash, OnboardingStatus, Recommendation, TaskExclusions } from "../api";
import OnboardingSplash from "../components/OnboardingSplash";
import OpenTasksByCompanyWidget from "../components/OpenTasksByCompanyWidget";
import TodayMeetingsWidget from "../components/TodayMeetingsWidget";

function needsOnboarding(status: OnboardingStatus | null): boolean {
  if (!status) return true;
  if (status.onboarding_complete === true) return false;
  if (status.onboarding_complete === false) return true;
  return !(status.google_connected && status.last_sync_at);
}

export default function DashboardPage() {
  const [onboarding, setOnboarding] = useState<OnboardingStatus | null>(null);
  const [data, setData] = useState<Dash | null>(null);
  const [checking, setChecking] = useState(false);

  const loadOnboarding = useCallback(async (): Promise<OnboardingStatus> => {
    try {
      return await api.onboardingStatus();
    } catch {
      try {
        const s = await api.settings();
        return {
          google_connected: s.google_connected,
          last_sync_at: s.last_sync_at,
          onboarding_complete:
            s.onboarding_complete ?? !!(s.google_connected && s.last_sync_at),
        };
      } catch {
        return {
          google_connected: false,
          last_sync_at: null,
          onboarding_complete: false,
        };
      }
    }
  }, []);

  const refresh = useCallback(async () => {
    setChecking(true);
    try {
      const status = await loadOnboarding();
      setOnboarding(status);
      if (!needsOnboarding(status)) {
        const dash = await api.dashboard();
        setData(dash);
      } else {
        setData(null);
      }
    } catch {
      setOnboarding({
        google_connected: false,
        last_sync_at: null,
        onboarding_complete: false,
      });
      setData(null);
    } finally {
      setChecking(false);
    }
  }, [loadOnboarding]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (!onboarding) {
    return <p className="text-gray-500">Loading…</p>;
  }

  if (needsOnboarding(onboarding)) {
    return (
      <OnboardingSplash
        googleConnected={onboarding.google_connected}
        hasSynced={!!onboarding.last_sync_at}
        onCheckAgain={refresh}
        checking={checking}
      />
    );
  }

  if (!data) {
    return <p className="text-gray-500">Loading dashboard…</p>;
  }

  return (
    <div className="space-y-8">
      <TodayMeetingsWidget
        initialMeetings={data.today_meetings ?? []}
        initialError={data.today_meetings_error ?? null}
      />

      <section>
        <h2 className="text-xl font-semibold mb-3">Focus for today</h2>
        {data.focus_today.length === 0 ? (
          <p className="text-gray-500 text-sm">No focus items yet.</p>
        ) : (
          <ul className="space-y-2">
            {data.focus_today.map((r) => (
              <FocusItem
                key={r.id}
                item={r}
                onDismiss={(id) =>
                  setData((prev) =>
                    prev
                      ? {
                          ...prev,
                          focus_today: prev.focus_today.filter((f) => f.id !== id),
                        }
                      : prev
                  )
                }
              />
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-3">Top recommendations</h2>
        <ul className="grid gap-2 md:grid-cols-2">
          {data.recommendations.map((r) => (
            <li key={r.id} className="bg-white border rounded p-3 text-sm">
              <p className="font-medium">{r.title}</p>
              {r.body && <p className="text-gray-600 mt-1">{r.body}</p>}
            </li>
          ))}
        </ul>
      </section>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        <OpenTasksByCompanyWidget
          companies={data.open_tasks_by_company}
          exclusions={data.task_exclusions ?? { emails: [], companies: [] }}
          onExclusionsChange={(next: TaskExclusions) =>
            setData((prev) => (prev ? { ...prev, task_exclusions: next } : prev))
          }
          onRefresh={async () => {
            const dash = await api.dashboard();
            setData(dash);
          }}
        />
        <Widget title="Aging (open tasks)">
          <ul className="text-sm space-y-1">
            {data.aging_buckets.map((b) => (
              <li key={b.label} className="flex justify-between">
                <span>{b.label}</span>
                <span className="font-mono">{b.count}</span>
              </li>
            ))}
          </ul>
        </Widget>
        <Widget title="Untouched 30+ days">
          <ul className="text-sm space-y-1 max-h-40 overflow-y-auto">
            {data.untouched_accounts_30d.map((a, i) => (
              <li key={i}>{a.company_name}</li>
            ))}
            {data.untouched_accounts_30d.length === 0 && (
              <li className="text-gray-500">None</li>
            )}
          </ul>
        </Widget>
        <Widget title="Sync health">
          <ul className="text-xs space-y-1">
            {data.sync_health.map((s) => (
              <li key={s.connector} className="border-b border-gray-100 pb-1 last:border-0">
                <div className="flex justify-between gap-2">
                  <span className="truncate">{s.connector}</span>
                  <span
                    className={
                      s.status === "success"
                        ? "text-green-700"
                        : s.status === "error"
                          ? "text-red-700"
                          : "text-gray-500"
                    }
                  >
                    {s.status}
                  </span>
                </div>
                {s.status === "error" && s.error_message && (
                  <p className="text-red-600 mt-0.5 line-clamp-3" title={s.error_message}>
                    {s.error_message}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </Widget>
      </div>
    </div>
  );
}

function FocusItem({
  item,
  onDismiss,
}: {
  item: Recommendation;
  onDismiss: (id: number) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleDismiss() {
    if (busy) return;
    setBusy(true);
    setErr(null);
    try {
      await api.dismissRecommendation(item.id);
      onDismiss(item.id);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Could not dismiss");
      setBusy(false);
    }
  }

  return (
    <li className="bg-white border rounded-lg p-3 shadow-sm flex items-start gap-3">
      <input
        type="checkbox"
        checked={false}
        disabled={busy}
        onChange={() => void handleDismiss()}
        aria-label={`Dismiss: ${item.title}`}
        className="mt-1 h-4 w-4 shrink-0 rounded border-gray-300 text-rh-red focus:ring-rh-red cursor-pointer disabled:opacity-50"
      />
      <div className="min-w-0">
        <span className="text-xs text-rh-red uppercase">{item.rec_type.replace(/_/g, " ")}</span>
        <p className="font-medium">{item.title}</p>
        {item.body && <p className="text-sm text-gray-600 mt-1">{item.body}</p>}
        {err && <p className="text-xs text-red-600 mt-1">{err}</p>}
      </div>
    </li>
  );
}

function Widget({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      <h3 className="font-medium text-sm text-gray-700 mb-2">{title}</h3>
      {children}
    </div>
  );
}
