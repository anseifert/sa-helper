import { Link, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Tasks from "./pages/Tasks";
import Contacts from "./pages/Contacts";
import SettingsPage from "./pages/Settings";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/tasks", label: "Tasks" },
  { to: "/contacts", label: "Contacts" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-rh-dark text-white shadow">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">
            SA Task Hub
          </h1>
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
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/contacts" element={<Contacts />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
