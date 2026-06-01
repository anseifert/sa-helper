import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Badge from "../components/Badge";
import { api, Task, TasksSummary } from "../api";

function removeTaskFromSummary(data: TasksSummary, taskId: number): TasksSummary {
  const stripTasks = (tasks: Task[]) => {
    const next = tasks.filter((t) => t.id !== taskId);
    return { tasks: next, task_count: next.length };
  };
  const mapAccount = (account: TasksSummary["priority_accounts"][0]) => {
    const { tasks, task_count } = stripTasks(account.tasks);
    return { ...account, tasks, task_count, summary: account.summary };
  };
  const mapCategory = (cat: TasksSummary["concur"]) => {
    const { tasks, task_count } = stripTasks(cat.tasks);
    return { ...cat, tasks, task_count };
  };
  return {
    priority_accounts: data.priority_accounts.map(mapAccount),
    concur: mapCategory(data.concur),
    redhat_direct: mapCategory(data.redhat_direct),
    other_accounts: data.other_accounts.map(mapAccount),
  };
}

function TaskRow({
  t,
  onComplete,
}: {
  t: Task;
  onComplete: (taskId: number) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleComplete() {
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      await onComplete(t.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not complete task");
      setBusy(false);
    }
  }

  return (
    <li className="bg-white border rounded-lg p-3 flex items-start gap-3">
      <input
        type="checkbox"
        checked={false}
        disabled={busy}
        onChange={() => void handleComplete()}
        aria-label={`Mark complete: ${t.title}`}
        className="mt-1 h-4 w-4 shrink-0 rounded border-gray-300 text-rh-red focus:ring-rh-red cursor-pointer disabled:opacity-50"
      />
      <div className="min-w-0 flex-1 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-medium">{t.title}</p>
          <p className="text-xs text-gray-500 mt-1">
            {t.task_type.replace(/_/g, " ")}
            {t.due_at && ` · due ${new Date(t.due_at).toLocaleDateString()}`}
          </p>
          {t.description && (
            <p className="text-sm text-gray-600 mt-2 line-clamp-2">{t.description}</p>
          )}
          {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
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
      </div>
    </li>
  );
}

function TaskSection({
  sectionId,
  title,
  summary,
  tasks,
  expanded,
  onComplete,
}: {
  sectionId: string;
  title: string;
  summary: string;
  tasks: Task[];
  expanded: boolean;
  onComplete: (taskId: number) => Promise<void>;
}) {
  const [open, setOpen] = useState(expanded);
  useEffect(() => {
    if (expanded) setOpen(true);
  }, [expanded]);

  if (tasks.length === 0) return null;
  return (
    <section id={`section-${sectionId}`} className="border rounded-lg bg-gray-50/80 scroll-mt-4">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 flex items-center justify-between gap-2"
      >
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <p className="text-sm text-gray-600 mt-0.5">{summary}</p>
        </div>
        <span className="text-sm font-mono text-gray-500 shrink-0">
          {tasks.length} {open ? "▾" : "▸"}
        </span>
      </button>
      {open && (
        <ul className="space-y-2 px-4 pb-4">
          {tasks.map((t) => (
            <TaskRow key={t.id} t={t} onComplete={onComplete} />
          ))}
        </ul>
      )}
    </section>
  );
}

export default function Tasks() {
  const [searchParams] = useSearchParams();
  const highlightSection = searchParams.get("section");
  const [data, setData] = useState<TasksSummary | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [showOther, setShowOther] = useState(false);

  useEffect(() => {
    api.tasksSummary().then(setData).catch((e) => setErr(String(e)));
  }, []);

  const handleComplete = useCallback(async (taskId: number) => {
    await api.completeTask(taskId);
    setData((prev) => (prev ? removeTaskFromSummary(prev, taskId) : prev));
  }, []);

  useEffect(() => {
    if (!data || !highlightSection) return;
    if (data.other_accounts.some((a) => a.account_key === highlightSection)) {
      setShowOther(true);
    }
  }, [data, highlightSection]);

  useEffect(() => {
    if (!data || !highlightSection) return;
    const timer = window.setTimeout(() => {
      document.getElementById(`section-${highlightSection}`)?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 150);
    return () => window.clearTimeout(timer);
  }, [data, highlightSection, showOther]);

  if (err) return <p className="text-red-600">{err}</p>;
  if (!data) return <p className="text-gray-500">Loading…</p>;

  const priorityWithWork = data.priority_accounts.filter((a) => a.task_count > 0);
  const totalPriority = priorityWithWork.reduce((n, a) => n + a.task_count, 0);
  const isExpanded = (sectionId: string) => highlightSection === sectionId;

  return (
    <div className="space-y-6 max-w-4xl">
      <p className="text-sm text-gray-600">
        Open tasks from the last 30 days — prioritized for ExxonMobil, ConocoPhillips,
        Windstream/Uniti, and EPP, plus Concur and direct Red Hat mail. Calendar invites
        appear on the dashboard under Today&apos;s meetings only. Threads whose subject
        starts with Re:, Notes:, or Invitation are excluded. Gmail tasks require your
        USER_EMAIL in To or Cc and exclude Google Groups recipients. Check a task to mark
        it complete.
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        {data.priority_accounts.map((account) => (
          <div
            key={account.account_key}
            className={`rounded-lg border p-4 ${
              account.task_count > 0 ? "bg-white" : "bg-gray-50 opacity-75"
            }`}
          >
            <h3 className="font-semibold">{account.display_name}</h3>
            <p className="text-2xl font-mono mt-1">{account.task_count}</p>
            <p className="text-xs text-gray-600 mt-1">{account.summary}</p>
          </div>
        ))}
      </div>

      {totalPriority === 0 &&
        data.concur.task_count === 0 &&
        data.redhat_direct.task_count === 0 && (
          <p className="text-gray-500">No open tasks in priority buckets. Run sync after connecting Google.</p>
        )}

      {priorityWithWork.map((account) => (
        <TaskSection
          key={account.account_key}
          sectionId={account.account_key}
          title={account.display_name}
          summary={account.summary}
          tasks={account.tasks}
          expanded={isExpanded(account.account_key)}
          onComplete={handleComplete}
        />
      ))}

      <TaskSection
        sectionId="concur"
        title={data.concur.label}
        summary={data.concur.summary}
        tasks={data.concur.tasks}
        expanded={isExpanded("concur")}
        onComplete={handleComplete}
      />

      <TaskSection
        sectionId="redhat_direct"
        title={data.redhat_direct.label}
        summary={data.redhat_direct.summary}
        tasks={data.redhat_direct.tasks}
        expanded={isExpanded("redhat_direct")}
        onComplete={handleComplete}
      />

      {data.other_accounts.length > 0 && (
        <section>
          <button
            type="button"
            onClick={() => setShowOther(!showOther)}
            className="text-sm font-medium text-rh-red hover:underline"
          >
            {showOther ? "Hide" : "Show"} other companies ({data.other_accounts.length})
          </button>
          {showOther && (
            <div className="space-y-4 mt-4">
              {data.other_accounts.map((account) => (
                <TaskSection
                  key={account.account_key}
                  sectionId={account.account_key}
                  title={account.display_name}
                  summary={account.summary}
                  tasks={account.tasks}
                  expanded={isExpanded(account.account_key)}
                  onComplete={handleComplete}
                />
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
