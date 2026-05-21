import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { api, AuthStatus } from "../api";

export default function RequireAuth() {
  const location = useLocation();
  const [status, setStatus] = useState<AuthStatus | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api
      .authMe()
      .then(setStatus)
      .catch(() => setFailed(true));
  }, []);

  if (failed || (status && !status.authenticated)) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (!status?.authenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Checking session…
      </div>
    );
  }

  return <Outlet />;
}
