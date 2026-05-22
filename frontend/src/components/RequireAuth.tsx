import { useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function RequireAuth() {
  const location = useLocation();
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .authMe()
      .then((status) => {
        if (cancelled) return;
        if (!status.authenticated) {
          navigate("/login", {
            replace: true,
            state: { from: location.pathname + location.search },
          });
          return;
        }
        setChecking(false);
      })
      .catch(() => {
        if (cancelled) return;
        navigate("/login", {
          replace: true,
          state: { from: location.pathname + location.search },
        });
      });
    return () => {
      cancelled = true;
    };
  }, [location.pathname, location.search, navigate]);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Checking session…
      </div>
    );
  }

  return <Outlet />;
}
