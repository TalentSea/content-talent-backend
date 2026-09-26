import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { getStoredToken } from "../services/apiService";

interface RequireAuthProps {
  children: ReactNode;
}

/**
 * Universal Authentication Route Guard.
 * Protects all administrative routes. If a user is not authenticated or has
 * explicitly logged out, access is completely blocked and they are redirected to /login.
 */
export default function RequireAuth({ children }: RequireAuthProps) {
  const location = useLocation();
  const token = getStoredToken();
  const isLoggedOut = typeof window !== "undefined" && localStorage.getItem("user_logged_out") === "true";

  if (!token || isLoggedOut) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
