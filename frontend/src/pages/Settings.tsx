import { useEffect, useState } from "react";
import { api, googleAuthUrl } from "../api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Awaited<ReturnType<typeof api.settings>> | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const load = () => api.settings().then(setSettings);

  useEffect(() => {
    load();
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "google") {
      setMsg("Google connected successfully.");
    }
    if (params.get("oauth_error") === "google") {
      setMsg("Google sign-in failed. Check server logs and try Connect Google again.");
    }
  }, []);

  const runSync = async () => {
    setSyncing(true);
    setMsg(null);
    try {
      await api.sync();
      setMsg("Sync completed.");
      await load();
    } catch (e) {
      setMsg(String(e));
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="max-w-lg space-y-6">
      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-semibold mb-2">Google</h2>
        <p className="text-sm text-gray-600 mb-3">
          Gmail (readonly), Calendar (readonly), Drive (readonly). Tokens stored encrypted on this machine.
        </p>
        {settings?.google_connected ? (
          <p className="text-green-700 text-sm mb-2">Connected</p>
        ) : (
          <a
            href={googleAuthUrl()}
            className="inline-block bg-rh-red text-white px-4 py-2 rounded text-sm"
          >
            Connect Google
          </a>
        )}
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-semibold mb-2">Sync</h2>
        <p className="text-sm text-gray-600 mb-2">
          Last sync: {settings?.last_sync_at ? new Date(settings.last_sync_at).toLocaleString() : "Never"}
        </p>
        <button
          type="button"
          onClick={runSync}
          disabled={syncing || !settings?.google_connected}
          className="bg-rh-dark text-white px-4 py-2 rounded text-sm disabled:opacity-50"
        >
          {syncing ? "Syncing…" : "Run sync now"}
        </button>
      </section>

      <section className="bg-white border rounded-lg p-4">
        <h2 className="font-semibold mb-2">Slack</h2>
        <p className="text-sm text-gray-600">
          {settings?.slack_configured
            ? "Token configured (extractor stub — no sync in MVP)."
            : "Set SLACK_BOT_TOKEN in .env (stub only in MVP)."}
        </p>
      </section>

      {msg && <p className="text-sm">{msg}</p>}
    </div>
  );
}
