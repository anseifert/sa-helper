import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  AssetCompany,
  AssetCompanyPatch,
  AssetsCatalog,
  AvailableCompany,
} from "../api";

function useDebouncedCallback(fn: () => void, delayMs: number) {
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  return useCallback(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => fnRef.current(), delayMs);
  }, [delayMs]);
}

function CompanyAssetsCard({
  company,
  catalog,
  onUpdate,
  onSaved,
}: {
  company: AssetCompany;
  catalog: AssetsCatalog;
  onUpdate: (id: number, patch: AssetCompanyPatch) => Promise<AssetCompany>;
  onSaved: (updated: AssetCompany) => void;
}) {
  const [open, setOpen] = useState(false);
  const [local, setLocal] = useState(company);
  const localRef = useRef(local);
  localRef.current = local;
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setLocal(company);
  }, [company]);

  const persist = useCallback(
    async (patch: AssetCompanyPatch) => {
      setSaving(true);
      setErr(null);
      try {
        const updated = await onUpdate(local.company_id, patch);
        setLocal(updated);
        onSaved(updated);
      } catch (e) {
        setErr(String(e));
      } finally {
        setSaving(false);
      }
    },
    [local.company_id, onUpdate, onSaved]
  );

  const debouncedPersist = useDebouncedCallback(() => {
    void persist({
      ansible_nodes: localRef.current.ansible_nodes,
      rhel_subscriptions: localRef.current.rhel_subscriptions,
    });
  }, 500);

  const toggleSub = (key: string, checked: boolean) => {
    const subscriptions = { ...local.subscriptions, [key]: checked };
    const next = { ...local, subscriptions };
    setLocal(next);
    void persist({ subscriptions });
  };

  const toggleHw = (key: string, checked: boolean) => {
    const hardware = { ...local.hardware, [key]: checked };
    const next = { ...local, hardware };
    setLocal(next);
    void persist({ hardware });
  };

  return (
    <section className="border rounded-lg bg-gray-50/80">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full text-left px-4 py-3 flex items-center justify-between gap-2"
      >
        <h2 className="text-lg font-semibold">{local.company_name}</h2>
        <span className="text-sm text-gray-500 shrink-0">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-100 pt-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Company name</label>
            <input
              type="text"
              value={local.company_name}
              onChange={(e) => setLocal({ ...local, company_name: e.target.value })}
              onBlur={() => {
                if (local.company_name.trim() && local.company_name !== company.company_name) {
                  void persist({ company_name: local.company_name.trim() });
                }
              }}
              className="border rounded px-2 py-1 text-sm w-full max-w-md"
            />
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Subscriptions</h3>
            <div className="flex flex-wrap gap-3">
              {catalog.subscriptions.map((item) => (
                <label key={item.key} className="flex items-center gap-1.5 text-sm">
                  <input
                    type="checkbox"
                    checked={!!local.subscriptions[item.key]}
                    onChange={(e) => toggleSub(item.key, e.target.checked)}
                  />
                  {item.label}
                </label>
              ))}
            </div>
          </div>

          <div className="flex flex-wrap gap-6">
            <label className="text-sm flex items-center gap-2">
              <span className="font-medium text-gray-700">Ansible Nodes</span>
              <input
                type="number"
                min={0}
                value={local.ansible_nodes}
                onChange={(e) => {
                  const v = Math.max(0, parseInt(e.target.value, 10) || 0);
                  setLocal({ ...local, ansible_nodes: v });
                  debouncedPersist();
                }}
                className="border rounded px-2 py-1 w-24 font-mono"
              />
            </label>
            <label className="text-sm flex items-center gap-2">
              <span className="font-medium text-gray-700">RHEL Subscriptions</span>
              <input
                type="number"
                min={0}
                value={local.rhel_subscriptions}
                onChange={(e) => {
                  const v = Math.max(0, parseInt(e.target.value, 10) || 0);
                  setLocal({ ...local, rhel_subscriptions: v });
                  debouncedPersist();
                }}
                className="border rounded px-2 py-1 w-24 font-mono"
              />
            </label>
          </div>

          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Hardware</h3>
            <div className="flex flex-wrap gap-3">
              {catalog.hardware.map((item) => (
                <label key={item.key} className="flex items-center gap-1.5 text-sm">
                  <input
                    type="checkbox"
                    checked={!!local.hardware[item.key]}
                    onChange={(e) => toggleHw(item.key, e.target.checked)}
                  />
                  {item.label}
                </label>
              ))}
            </div>
          </div>

          {saving && <p className="text-xs text-gray-500">Saving…</p>}
          {err && <p className="text-xs text-red-600">{err}</p>}
        </div>
      )}
    </section>
  );
}

export default function Assets() {
  const [catalog, setCatalog] = useState<AssetsCatalog | null>(null);
  const [companies, setCompanies] = useState<AssetCompany[]>([]);
  const [available, setAvailable] = useState<AvailableCompany[]>([]);
  const [pickId, setPickId] = useState<number | "">("");
  const [err, setErr] = useState<string | null>(null);

  const reload = useCallback(() => {
    Promise.all([api.assetsCatalog(), api.assets(), api.assetsAvailableCompanies()])
      .then(([cat, list, avail]) => {
        setCatalog(cat);
        setCompanies(list);
        setAvailable(avail);
        setErr(null);
      })
      .catch((e) => setErr(String(e)));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const handleUpdate = useCallback(
    (id: number, patch: AssetCompanyPatch) => api.updateAssetCompany(id, patch),
    []
  );

  const handleSaved = useCallback((updated: AssetCompany) => {
    setCompanies((prev) =>
      prev.map((c) => (c.company_id === updated.company_id ? updated : c))
    );
  }, []);

  const attach = async () => {
    if (pickId === "") return;
    try {
      await api.attachAssetCompany(pickId);
      setPickId("");
      reload();
    } catch (e) {
      setErr(String(e));
    }
  };

  if (err && !catalog) return <p className="text-red-600">{err}</p>;
  if (!catalog) return <p className="text-gray-500">Loading…</p>;

  return (
    <div className="space-y-6 max-w-4xl">
      <p className="text-sm text-gray-600">
        Track subscriptions and hardware by company. Add companies that already exist in the app
        (from sync or contacts). Changes save automatically.
      </p>

      {available.length > 0 && (
        <div className="flex flex-wrap gap-2 items-end bg-white border rounded-lg p-4">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Add company to Assets
            </label>
            <select
              value={pickId}
              onChange={(e) =>
                setPickId(e.target.value === "" ? "" : Number(e.target.value))
              }
              className="border rounded px-3 py-2 text-sm w-full"
            >
              <option value="">Select a company…</option>
              {available.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            onClick={attach}
            disabled={pickId === ""}
            className="bg-rh-dark text-white px-4 py-2 rounded text-sm disabled:opacity-50"
          >
            Add
          </button>
        </div>
      )}

      {err && <p className="text-sm text-amber-700">{err}</p>}

      <div className="space-y-4">
        {companies.length === 0 ? (
          <p className="text-gray-500 text-sm">No companies on Assets yet.</p>
        ) : (
          companies.map((c) => (
            <CompanyAssetsCard
              key={c.company_id}
              company={c}
              catalog={catalog}
              onUpdate={handleUpdate}
              onSaved={handleSaved}
            />
          ))
        )}
      </div>
    </div>
  );
}
