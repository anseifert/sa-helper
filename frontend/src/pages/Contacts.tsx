import { useEffect, useState } from "react";
import { api, Contact } from "../api";

export default function Contacts() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [q, setQ] = useState("");
  const [companies, setCompanies] = useState<{ id: number; name: string }[]>([]);
  const [companyFilter, setCompanyFilter] = useState<number | "">("");
  const [err, setErr] = useState<string | null>(null);

  const load = () => {
    api
      .contacts(q || undefined, companyFilter === "" ? undefined : companyFilter)
      .then(setContacts)
      .catch((e) => setErr(String(e)));
  };

  useEffect(() => {
    api.companies().then(setCompanies);
  }, []);

  useEffect(() => {
    load();
  }, [companyFilter]);

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load();
  };

  const overrideCompany = async (c: Contact, value: string) => {
    await api.updateContact(c.id, { company_override: value || undefined });
    load();
  };

  const enrich = async (id: number) => {
    await api.enrichContact(id);
    load();
  };

  if (err) return <p className="text-red-600">{err}</p>;

  return (
    <div>
      <form onSubmit={onSearch} className="flex flex-wrap gap-2 mb-4">
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
        <button
          type="submit"
          className="bg-rh-dark text-white px-4 py-2 rounded text-sm"
        >
          Search
        </button>
      </form>

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
            {contacts.map((c) => (
              <tr key={c.id} className="border-t">
                <td className="p-2 font-mono text-xs">{c.email}</td>
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
                    className="border rounded px-2 py-1 w-full max-w-[140px]"
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
                <td className="p-2">
                  <button
                    type="button"
                    onClick={() => enrich(c.id)}
                    className="text-xs text-rh-red hover:underline"
                  >
                    Enrich
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
