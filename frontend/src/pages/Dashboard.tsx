import { useEffect, useState } from "react";
import { api, Dashboard as Dash } from "../api";

export default function DashboardPage() {
  const [data, setData] = useState<Dash | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <p className="text-red-600">{err}</p>;
  if (!data) return <p className="text-gray-500">Loading…</p>;

  return (
    <div className="space-y-8">
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
        <Widget title="Open tasks by company">
          <ul className="text-sm space-y-1">
            {data.open_tasks_by_company.map((c, i) => (
              <li key={i} className="flex justify-between">
                <span>{c.company_name}</span>
                <span className="font-mono">{c.count}</span>
              </li>
            ))}
          </ul>
        </Widget>
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
              <li key={s.connector} className="flex justify-between gap-2">
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
