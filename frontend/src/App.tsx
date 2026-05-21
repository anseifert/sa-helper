import { Link, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import RequireAuth from "./components/RequireAuth";
import Dashboard from "./pages/Dashboard";
import Tasks from "./pages/Tasks";
import Contacts from "./pages/Contacts";
import SettingsPage from "./pages/Settings";
import Login from "./pages/Login";
import { api } from "./api";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/tasks", label: "Tasks" },
  { to: "/contacts", label: "Contacts" },
  { to: "/settings", label: "Settings" },
];

function AppShell() {
  const navigate = useNavigate();

  const logout = async () => {
    try {
      await api.logout();
    } finally {
      navigate("/login", { replace: true });
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-rh-dark text-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">SA Task Hub</h1>
          <div className="flex items-center gap-4">
            <nav className="flex gap-4 text-sm">
              {nav.map((n) => (
                <Link
                  key={n.to}
                  to={n.to}
                  className="hover:text-red-300 transition-colors"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
            <button
              type="button"
              onClick={logout}
              className="text-sm text-gray-300 hover:text-white"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route index element={<Dashboard />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="contacts" element={<Contacts />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
