import { useEffect, useState } from "react";
import { api, Contact } from "../api";

export default function Contacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [q, setQ] = useState("");
  const [companies, setCompanies] = useState<{ id: number; name: string }[]>([]);
  const [companyFilter, setCompanyFilter] = useState<number | "">("");
  const [showIgnored, setShowIgnored] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = () => {
    api
      .contacts(
        q || undefined,
        companyFilter === "" ? undefined : companyFilter,
        showIgnored
      )
      .then(setContacts)
      .catch((e) => setErr(String(e)));
  };

  useEffect(() => {
    api.companies().then(setCompanies);
  }, []);

  useEffect(() => {
    load();
  }, [companyFilter, showIgnored]);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load();
  };

  const overrideCompany = async (c: Contact, value: string) => {
    await api.updateContact(c.id, { company_override: value || undefined });
    load();
  };

  const setIgnored = async (c: Contact, ignored: boolean) => {
    await api.updateContact(c.id, { is_ignored: ignored });
    load();
  };

  const enrich = async (id: number) => {
    await api.enrichContact(id);
    load();
  };

  if (err) return <p className="text-red-600">{err}</p>;

  const visibleCount = contacts.filter((c) => !c.is_ignored).length;
  const ignoredCount = contacts.filter((c) => c.is_ignored).length;

  return (
    <div>
      <p className="text-sm text-gray-600 mb-4">
        Ignored contacts stay in the system for sync and tasks but are hidden from this list.
        Use <strong>Show ignored</strong> to view or restore them.
      </p>

      <form onSubmit={onSearch} className="flex flex-wrap gap-2 mb-4 items-center">
        <input
          type="search"
          placeholder="Search email or name…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="border rounded px-3 py-2 text-sm flex-1 min-w-[200px]"
        />
        <select
          value={companyFilter}
          onChange={(e) =>
            setCompanyFilter(e.target.value === "" ? "" : Number(e.target.value))
          }
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="">All companies</option>
          {companies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input
            type="checkbox"
            checked={showIgnored}
            onChange={(e) => setShowIgnored(e.target.checked)}
          />
          Show ignored
          {showIgnored && ignoredCount > 0 && (
            <span className="text-gray-500">({ignoredCount})</span>
          )}
        </label>
        <button
          type="submit"
          className="bg-rh-dark text-white px-4 py-2 rounded text-sm"
        >
          Search
        </button>
      </form>

      {!showIgnored && (
        <p className="text-xs text-gray-500 mb-2">
          Showing {visibleCount} contact{visibleCount === 1 ? "" : "s"}
        </p>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm bg-white border rounded-lg">
          <thead className="bg-gray-100 text-left">
            <tr>
              <th className="p-2">Email</th>
              <th className="p-2">Name</th>
              <th className="p-2">Company</th>
              <th className="p-2">Override</th>
              <th className="p-2">Title / Notes</th>
              <th className="p-2"></th>
            </tr>
          </thead>
          <tbody>
            {contacts.length === 0 ? (
              <tr>
                <td colSpan={6} className="p-4 text-gray-500 text-center">
                  No contacts match your filters.
                </td>
              </tr>
            ) : (
              contacts.map((c) => (
                <tr
                  key={c.id}
                  className={`border-t ${c.is_ignored ? "bg-gray-50 opacity-70" : ""}`}
                >
                  <td className="p-2 font-mono text-xs">
                    {c.email}
                    {c.is_ignored && (
                      <span className="ml-2 text-xs text-amber-700 font-sans">ignored</span>
                    )}
                  </td>
                  <td className="p-2">{c.display_name || "—"}</td>
                  <td className="p-2">
                    {c.company_name || "—"}
                    {c.is_internal && (
                      <span className="ml-1 text-xs text-gray-500">(internal)</span>
                    )}
                  </td>
                  <td className="p-2">
                    <input
                      type="text"
                      defaultValue={c.company_override || ""}
                      placeholder="Override…"
                      disabled={c.is_ignored}
                      className="border rounded px-2 py-1 w-full max-w-[140px] disabled:bg-gray-100"
                      onBlur={(e) => {
                        if (e.target.value !== (c.company_override || "")) {
                          overrideCompany(c, e.target.value);
                        }
                      }}
                    />
                  </td>
                  <td className="p-2 text-gray-600">
                    {c.title && <div>{c.title}</div>}
                    {c.notes && <div className="text-xs">{c.notes}</div>}
                  </td>
                  <td className="p-2 space-y-1">
                    {c.is_ignored ? (
                      <button
                        type="button"
                        onClick={() => setIgnored(c, false)}
                        className="text-xs text-rh-red hover:underline block"
                      >
                        Restore
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          onClick={() => setIgnored(c, true)}
                          className="text-xs text-gray-600 hover:underline block"
                        >
                          Ignore
                        </button>
                        <button
                          type="button"
                          onClick={() => enrich(c.id)}
                          className="text-xs text-rh-red hover:underline block"
                        >
                          Enrich
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
