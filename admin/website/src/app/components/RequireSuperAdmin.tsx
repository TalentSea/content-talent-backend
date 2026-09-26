import { ReactNode, useEffect, useRef } from "react";
import { Navigate, useLocation } from "react-router";
import { getStoredAdmin } from "../services/apiService";
import { toast } from "sonner";

interface RequireSuperAdminProps {
  children: ReactNode;
}

/**
 * Route Guard Component for Platform Super Admin pages.
 * Strictly enforces role === "super_admin". Unauthorized users are bounced to dashboard
 * with an access-denied alert toast.
 */
export default function RequireSuperAdmin({ children }: RequireSuperAdminProps) {
  const location = useLocation();
  const storedAdmin = getStoredAdmin();
  const hasAlertedRef = useRef(false);

  const isSuperAdmin = storedAdmin?.role === "super_admin";

  useEffect(() => {
    if (!isSuperAdmin && !hasAlertedRef.current) {
      hasAlertedRef.current = true;
      toast.error("Access Denied: Platform Super Admin privileges required.");
    }
  }, [isSuperAdmin]);

  if (!isSuperAdmin) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
