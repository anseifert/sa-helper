import { useState } from "react";
import { Link } from "react-router-dom";
import { api, Dashboard, TaskExclusions } from "../api";

type Props = {
  companies: Dashboard["open_tasks_by_company"];
  exclusions: TaskExclusions;
  onExclusionsChange: (next: TaskExclusions) => void;
  onRefresh: () => void;
};

export default function OpenTasksByCompanyWidget({
  companies,
  exclusions,
  onExclusionsChange,
  onRefresh,
}: Props) {
  const [customize, setCustomize] = useState(false);
  const [emailInput, setEmailInput] = useState("");
  const [companyInput, setCompanyInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasRules = exclusions.emails.length > 0 || exclusions.companies.length > 0;

  async function persist(next: TaskExclusions) {
    setSaving(true);
    setError(null);
    try {
      const saved = await api.updateTaskExclusions(next);
      onExclusionsChange(saved);
      onRefresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setSaving(false);
    }
  }

  function addEmail() {
    const v = emailInput.trim().toLowerCase();
    if (!v) return;
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v)) {
      setError("Enter a valid email address.");
      return;
    }
    if (exclusions.emails.includes(v)) {
      setEmailInput("");
      return;
    }
    const next = { ...exclusions, emails: [...exclusions.emails, v] };
    setEmailInput("");
    void persist(next);
  }

  function addCompany() {
    const v = companyInput.trim();
    if (!v) return;
    const key = v.includes("@") ? v.split("@").pop()!.toLowerCase() : v.toLowerCase();
    if (exclusions.companies.some((c) => c === key)) {
      setCompanyInput("");
      return;
    }
    const next = { ...exclusions, companies: [...exclusions.companies, key] };
    setCompanyInput("");
    void persist(next);
  }

  function removeEmail(email: string) {
    void persist({
      ...exclusions,
      emails: exclusions.emails.filter((e) => e !== email),
    });
  }

  function removeCompany(company: string) {
    void persist({
      ...exclusions,
      companies: exclusions.companies.filter((c) => c !== company),
    });
  }

  return (
    <div className="bg-white border rounded-lg p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="font-medium text-sm text-gray-700">Open tasks by company</h3>
        <button
          type="button"
          onClick={() => setCustomize(!customize)}
          className="text-xs text-rh-red hover:underline shrink-0"
        >
          {customize ? "Done" : "Customize"}
        </button>
      </div>

      {hasRules && !customize && (
        <p className="text-xs text-gray-500 mb-2">
          {exclusions.emails.length} email
          {exclusions.emails.length === 1 ? "" : "s"} and {exclusions.companies.length} company
          {exclusions.companies.length === 1 ? "" : " targets"} excluded
        </p>
      )}

      <ul className="text-sm space-y-1">
        {companies.length === 0 ? (
          <li className="text-gray-500">No open tasks in window</li>
        ) : (
          companies.map((c) => (
            <li key={c.company_id ?? "unassigned"}>
              <Link
                to={`/tasks?section=${encodeURIComponent(c.section_id ?? c.company_name.toLowerCase().replace(/ /g, "_"))}`}
                className="flex justify-between gap-2 rounded px-1 -mx-1 hover:bg-gray-50 text-inherit hover:text-rh-red"
              >
                <span className="truncate hover:underline">{c.company_name}</span>
                <span className="font-mono shrink-0">{c.count}</span>
              </Link>
            </li>
          ))
        )}
      </ul>

      {customize && (
        <div className="mt-4 pt-3 border-t border-gray-100 space-y-4 text-xs">
          <p className="text-gray-600">
            Hide open tasks linked to a specific contact email, or tied to a company name or
            domain (e.g. <span className="font-mono">acme.com</span> or{" "}
            <span className="font-mono">Acme Corp</span>).
          </p>

          <div>
            <label className="block font-medium text-gray-700 mb-1">Exclude email</label>
            <div className="flex gap-1">
              <input
                type="email"
                value={emailInput}
                onChange={(e) => setEmailInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addEmail()}
                placeholder="person@company.com"
                className="flex-1 border rounded px-2 py-1 text-sm"
                disabled={saving}
              />
              <button
                type="button"
                onClick={addEmail}
                disabled={saving}
                className="px-2 py-1 bg-rh-red text-white rounded text-sm disabled:opacity-50"
              >
                Add
              </button>
            </div>
            {exclusions.emails.length > 0 && (
              <ul className="mt-2 space-y-1">
                {exclusions.emails.map((email) => (
                  <li key={email} className="flex justify-between gap-2 bg-gray-50 rounded px-2 py-1">
                    <span className="font-mono truncate">{email}</span>
                    <button
                      type="button"
                      onClick={() => removeEmail(email)}
                      disabled={saving}
                      className="text-red-600 hover:underline shrink-0"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <label className="block font-medium text-gray-700 mb-1">Exclude company</label>
            <div className="flex gap-1">
              <input
                type="text"
                value={companyInput}
                onChange={(e) => setCompanyInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addCompany()}
                placeholder="domain.com or Company Name"
                className="flex-1 border rounded px-2 py-1 text-sm"
                disabled={saving}
              />
              <button
                type="button"
                onClick={addCompany}
                disabled={saving}
                className="px-2 py-1 bg-rh-red text-white rounded text-sm disabled:opacity-50"
              >
                Add
              </button>
            </div>
            {exclusions.companies.length > 0 && (
              <ul className="mt-2 space-y-1">
                {exclusions.companies.map((company) => (
                  <li
                    key={company}
                    className="flex justify-between gap-2 bg-gray-50 rounded px-2 py-1"
                  >
                    <span className="truncate">{company}</span>
                    <button
                      type="button"
                      onClick={() => removeCompany(company)}
                      disabled={saving}
                      className="text-red-600 hover:underline shrink-0"
                    >
                      Remove
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {error && <p className="text-red-600">{error}</p>}
          {saving && <p className="text-gray-500">Saving…</p>}
        </div>
      )}
    </div>
  );
}
