import { useCallback, useEffect, useState } from "react";
import { api, Dashboard as Dash, TaskExclusions } from "../api";
import OnboardingSplash from "../components/OnboardingSplash";
import OpenTasksByCompanyWidget from "../components/OpenTasksByCompanyWidget";
import TodayMeetingsWidget from "../components/TodayMeetingsWidget";

export default function DashboardPage() {
  const [onboarding, setOnboarding] = useState<{
    google_connected: boolean;
    last_sync_at: string | null;
    onboarding_complete: boolean;
  } | null>(null);
  const [data, setData] = useState<Dash | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  const loadSettings = useCallback(() => {
    return api.settings().then((s) => {
      setOnboarding({
        google_connected: s.google_connected,
        last_sync_at: s.last_sync_at,
        onboarding_complete: s.onboarding_complete,
      });
      return s;
    });
  }, []);

  const loadDashboard = useCallback(() => {
    return api.dashboard().then(setData).catch((e) => setErr(String(e)));
  }, []);

  const refresh = useCallback(async () => {
    setErr(null);
    setChecking(true);
    try {
      const s = await loadSettings();
      if (s.onboarding_complete) {
        await loadDashboard();
      } else {
        setData(null);
      }
    } catch (e) {
      setErr(String(e));
    } finally {
      setChecking(false);
    }
  }, [loadSettings, loadDashboard]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (!onboarding && !err) {
    return <p className="text-gray-500">Loading…</p>;
  }

  if (err && !onboarding) {
    return <p className="text-red-600">{err}</p>;
  }

  if (onboarding && !onboarding.onboarding_complete) {
    return (
      <OnboardingSplash
        googleConnected={onboarding.google_connected}
        hasSynced={!!onboarding.last_sync_at}
        onCheckAgain={refresh}
        checking={checking}
      />
    );
  }

  if (err) return <p className="text-red-600">{err}</p>;
  if (!data) return <p className="text-gray-500">Loading dashboard…</p>;

  return (
    <div className="space-y-8">
      <TodayMeetingsWidget
        meetings={data.today_meetings ?? []}
        error={data.today_meetings_error ?? null}
      />

      <section>
        <h2 className="text-xl font-semibold mb-3">Focus for today</h2>
        {data.focus_today.length === 0 ? (
          <p className="text-gray-500 text-sm">No focus items yet — run sync after connecting Google.</p>
        ) : (
          <ul className="space-y-2">
            {data.focus_today.map((r) => (
              <li key={r.id} className="bg-white border rounded-lg p-3 shadow-sm">
                <span className="text-xs text-rh-red uppercase">{r.rec_type.replace(/_/g, " ")}</span>
                <p className="font-medium">{r.title}</p>
                {r.body && <p className="text-sm text-gray-600 mt-1">{r.body}</p>}
              </li>
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
          onRefresh={loadDashboard}
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
