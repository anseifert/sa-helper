import { useEffect, useState } from "react";
import Badge from "../components/Badge";
import { api, TaskGroup } from "../api";

export default function Tasks() {
  const [groups, setGroups] = useState<TaskGroup[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.tasks().then(setGroups).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <p className="text-red-600">{err}</p>;

  return (
    <div>
      <p className="text-sm text-gray-600 mb-4">
        Open tasks from the last 30 days, grouped by company (oldest first).
      </p>
      {groups.length === 0 ? (
        <p className="text-gray-500">No open tasks. Connect Google and run sync.</p>
      ) : (
        <div className="space-y-6">
          {groups.map((g) => (
            <section key={g.company_key}>
              <h2 className="text-lg font-semibold border-b pb-1 mb-3">
                {g.company_name}
                <span className="text-sm font-normal text-gray-500 ml-2">
                  ({g.tasks.length})
                </span>
              </h2>
              <ul className="space-y-2">
                {g.tasks.map((t) => (
                  <li
                    key={t.id}
                    className="bg-white border rounded-lg p-3 flex items-start justify-between gap-3"
                  >
                    <div>
                      <p className="font-medium">{t.title}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {t.task_type.replace(/_/g, " ")}
                        {t.due_at && ` · due ${new Date(t.due_at).toLocaleDateString()}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge source={t.badge_source} />
                      {t.origin_url && (
                        <a
                          href={t.origin_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm text-rh-red hover:underline"
                        >
                          Open
                        </a>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
