import { createBrowserRouter, useRouteError } from "react-router";
import Dashboard from "./pages/Dashboard";
import ContentManagement from "./pages/ContentManagement";
import Subscribers from "./pages/Subscribers";
import SubscriptionPlans from "./pages/SubscriptionPlans";
import Analytics from "./pages/Analytics";
import Revenue from "./pages/Revenue";
import Community from "./pages/Community";
import Branding from "./pages/Branding";
import Categories from "./pages/Categories";
import Settings from "./pages/Settings";
import AdminLayout from "./components/AdminLayout";
import Login from "./pages/Login";
import AppPublishing from "./pages/AppPublishing";

function RouteErrorBoundary() {
  const error: any = useRouteError();
  console.error("Route error caught:", error);
  return (
    <div className="flex flex-col items-center justify-center min-h-[450px] p-6 text-center">
      <div className="bg-white border border-slate-200 p-8 rounded-2xl max-w-lg w-full shadow-lg">
        <div className="h-12 w-12 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center mx-auto mb-4 text-rose-600 text-xl font-bold font-mono">
          !
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">Application Notice</h2>
        <p className="text-sm text-slate-500 mb-6">
          {error?.message || "A rendering exception occurred on this screen. Reloading may resolve the state."}
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => window.location.reload()}
            className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-semibold transition-colors shadow-xs cursor-pointer"
          >
            Reload Screen
          </button>
          <a
            href="/"
            className="px-5 py-2.5 bg-white hover:bg-slate-50 text-slate-700 rounded-xl text-sm font-semibold transition-colors border border-slate-200 shadow-xs cursor-pointer"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

import SuperAdminCenter from "./pages/SuperAdminCenter";
import RequireSuperAdmin from "./components/RequireSuperAdmin";
import RequireAuth from "./components/RequireAuth";

function GuardedAdminLayout() {
  return (
    <RequireAuth>
      <AdminLayout />
    </RequireAuth>
  );
}

function GuardedSuperAdminCenter() {
  return (
    <RequireSuperAdmin>
      <SuperAdminCenter />
    </RequireSuperAdmin>
  );
}

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/",
    Component: GuardedAdminLayout,
    ErrorBoundary: RouteErrorBoundary,
    children: [
      { index: true, Component: Dashboard },
      { path: "content", Component: ContentManagement },
      { path: "subscribers", Component: Subscribers },
      { path: "plans", Component: SubscriptionPlans },
      { path: "analytics", Component: Analytics },
      { path: "revenue", Component: Revenue },
      { path: "community", Component: Community },
      { path: "branding", Component: Branding },
      { path: "categories", Component: Categories },
      { path: "settings", Component: Settings },
      { path: "mobile-apps", Component: AppPublishing },
      { path: "super-admin", Component: GuardedSuperAdminCenter },
    ],
  },
]);

