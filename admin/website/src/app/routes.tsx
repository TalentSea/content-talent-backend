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

function RouteErrorBoundary() {
  const error: any = useRouteError();
  console.error("Route error caught:", error);
  return (
    <div className="flex flex-col items-center justify-center min-h-[450px] p-6 text-center">
      <div className="bg-slate-900/80 border border-slate-800 p-8 rounded-2xl max-w-lg w-full shadow-2xl backdrop-blur-xl">
        <div className="h-12 w-12 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-4 text-rose-400 text-xl font-bold font-mono">
          !
        </div>
        <h2 className="text-xl font-bold text-white mb-2">Application Notice</h2>
        <p className="text-sm text-slate-400 mb-6">
          {error?.message || "A rendering exception occurred on this screen. Reloading may resolve the state."}
        </p>
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => window.location.reload()}
            className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-xl text-sm font-medium transition-colors shadow-lg shadow-purple-600/30"
          >
            Reload Screen
          </button>
          <a
            href="/"
            className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-sm font-medium transition-colors border border-slate-700"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/",
    Component: AdminLayout,
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
    ],
  },
]);

