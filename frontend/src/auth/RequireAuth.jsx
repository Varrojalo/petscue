import { Navigate, useLocation } from "react-router";

import { Loading } from "../components/PageState";
import { useAuth } from "./AuthProvider";

/** Panel pages need a signed-in account; otherwise go to the login and come back here afterwards. */
export function RequireAuth({ children }) {
  const { user, loading, expired } = useAuth();
  const location = useLocation();
  if (loading) return <Loading />;
  if (!user) return <Navigate to="/dashboard/login" replace state={{ from: location.pathname + location.search, expired }} />;
  return children;
}

/** Sections only the administration role can open. */
export function RequireAdmin({ children }) {
  const { user } = useAuth();
  if (user?.role !== "admin") return <Navigate to="/dashboard" replace />;
  return children;
}
