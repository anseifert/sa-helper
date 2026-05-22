import { FormEvent, useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Login() {
  const location = useLocation();
  const navigate = useNavigate();
  const from = (location.state as { from?: string } | null)?.from ?? "/";
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loginConfigured, setLoginConfigured] = useState(true);

  useEffect(() => {
    api
      .authMe()
      .then((status) => {
        setLoginConfigured(status.login_configured);
        if (status.authenticated) {
          navigate(from, { replace: true });
        }
      })
      .catch(() => setLoginConfigured(false));
  }, [from, navigate]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      await api.login(username, password);
      // Full navigation so the session cookie is sent on the next page load.
      window.location.assign(from);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Login failed");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-md bg-white border rounded-lg shadow-sm p-6">
        <h1 className="text-xl font-semibold text-rh-dark">SA Task Hub</h1>
        <p className="text-sm text-gray-600 mt-1 mb-4">Sign in to continue</p>

        {!loginConfigured && (
          <div className="mb-4 rounded border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
            <p className="font-medium">Login not configured on the server</p>
            <p className="mt-1">
              On the machine running Docker, edit the <code className="text-xs">.env</code>{" "}
              file in the project folder and set:
            </p>
            <pre className="mt-2 text-xs bg-white border rounded p-2 overflow-x-auto">
              APP_USERNAME=admin{"\n"}
              APP_PASSWORD=your-chosen-password
            </pre>
            <p className="mt-2">
              Then run <code className="text-xs">docker compose up -d --build</code> and use
              that password here.
            </p>
          </div>
        )}

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full border rounded px-3 py-2 text-sm"
              required
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full border rounded px-3 py-2 text-sm"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Must match <code>APP_PASSWORD</code> in the server <code>.env</code> file (not
              Google OAuth).
            </p>
          </div>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button
            type="submit"
            disabled={loading || !loginConfigured}
            className="w-full bg-rh-red text-white py-2 rounded text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="text-xs text-gray-500 mt-4">
          Direct link:{" "}
          <a href="/login" className="text-rh-red hover:underline">
            /login
          </a>
        </p>
      </div>
    </div>
  );
}
