import { Outlet, Link, useLocation, useNavigate } from "react-router";
import {
  LayoutDashboard, Video, Users, CreditCard, BarChart3, DollarSign,
  MessageSquare, Palette, FolderTree, Settings, Menu, Bell,
  Search, User, LogOut, Camera, Mail, Phone, MapPin, Loader2,
  PanelLeftClose, PanelLeftOpen, ShieldCheck, ChevronsUpDown, Check, Building2,
} from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Avatar, AvatarFallback, AvatarImage } from "./ui/avatar";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import {
  Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription,
} from "./ui/dialog";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import ApiResponseMonitor from "./ApiResponseMonitor";
import {
  getCreatorProfile,
  updateCreatorProfile,
  getDashboardStats,
  getCreatorBranding,
  adminGetMe,
  adminRefresh,
  adminLogout,
  getStoredAdmin,
  getStoredToken,
  clearStoredAuth,
  getTenants,
  ApiTenant,
} from "../services/apiService";
import SuperAdminDashboard from "../pages/SuperAdminDashboard";

const navigation = [
  { name: "Dashboard", path: "/", icon: LayoutDashboard },
  { name: "Content", path: "/content", icon: Video },
  { name: "Subscribers", path: "/subscribers", icon: Users },
  { name: "Plans", path: "/plans", icon: CreditCard },
  { name: "Analytics", path: "/analytics", icon: BarChart3 },
  { name: "Revenue", path: "/revenue", icon: DollarSign },
  { name: "Community", path: "/community", icon: MessageSquare },
  { name: "Branding", path: "/branding", icon: Palette },
  { name: "Categories", path: "/categories", icon: FolderTree },
  { name: "Settings", path: "/settings", icon: Settings },
];

function ProfileDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [stats, setStats] = useState<{ videos: number; subscribers: number; views: number }>({
    videos: 0,
    subscribers: 0,
    views: 0,
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    Promise.all([
      getCreatorProfile().catch(() => null),
      getDashboardStats().catch(() => null),
    ])
      .then(([profile, dashStats]) => {
        if (profile) {
          setName(profile.fullName || `${profile.firstName || ""} ${profile.lastName || ""}`.trim() || "Creator");
          setEmail(profile.email || "");
          setPhone(profile.phone || "");
          setLocation(profile.location || "");
          setBio(profile.bio || "");
          setAvatarUrl(profile.avatarUrl || "");
        }
        if (dashStats) {
          setStats({
            videos: dashStats.totalContent?.total || 0,
            subscribers: dashStats.totalSubscribers?.current || 0,
            views: dashStats.totalViews?.current || 0,
          });
        }
      })
      .finally(() => setLoading(false));
  }, [open]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateCreatorProfile({
        first_name: name,
        phone,
        location,
        bio,
      });
      setSaved(true);
      setTimeout(() => {
        setSaved(false);
        onClose();
      }, 800);
    } catch (err) {
      console.warn("Failed to save profile from modal", err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg bg-white border border-slate-200 text-slate-900 shadow-2xl">
        <DialogHeader>
          <DialogTitle className="text-slate-900">My Profile</DialogTitle>
          <DialogDescription className="text-slate-500">Manage your personal information and studio profile</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-500 gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-slate-900" />
            <p className="text-sm">Loading profile...</p>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Avatar */}
            <div className="flex items-center gap-4">
              <div className="relative">
                {avatarUrl ? (
                  <img src={avatarUrl} alt={name} className="h-20 w-20 rounded-full object-cover border border-slate-200 shadow-xs" />
                ) : (
                  <div className="h-20 w-20 rounded-full bg-slate-900 flex items-center justify-center text-white text-2xl font-bold shadow-xs">
                    {(name || "C").charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-semibold text-slate-900">{name || "Creator"}</p>
                <p className="text-sm text-slate-500">{email}</p>
              </div>
            </div>

            {/* Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-700 text-xs"><User className="h-3.5 w-3.5 text-slate-500" />Display Name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-700 text-xs"><Mail className="h-3.5 w-3.5 text-slate-500" />Email</Label>
                <Input type="email" value={email} disabled className="bg-slate-50 border-slate-200 text-slate-500 cursor-not-allowed" />
              </div>
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-700 text-xs"><Phone className="h-3.5 w-3.5 text-slate-500" />Phone</Label>
                <Input value={phone} onChange={(e) => setPhone(e.target.value)} />
              </div>
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-700 text-xs"><MapPin className="h-3.5 w-3.5 text-slate-500" />Location</Label>
                <Input value={location} onChange={(e) => setLocation(e.target.value)} />
              </div>
            </div>
            <div>
              <Label className="mb-1 block text-slate-700 text-xs">Bio</Label>
              <textarea
                className="w-full border border-slate-200 rounded-xl p-3 text-sm text-slate-900 bg-white resize-none outline-none focus:border-slate-900 focus:ring-1 focus:ring-slate-900 transition-colors shadow-2xs"
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
              />
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-3 bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-center">
              {[
                { label: "Videos", value: stats.videos.toLocaleString() },
                { label: "Subscribers", value: stats.subscribers.toLocaleString() },
                { label: "Total Views", value: stats.views.toLocaleString() },
              ].map((s) => (
                <div key={s.label}>
                  <div className="font-bold text-slate-900 text-base">{s.value}</div>
                  <div className="text-xs text-slate-500">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving || loading} className={saved ? "bg-emerald-600 hover:bg-emerald-500 text-white" : "bg-slate-900 hover:bg-slate-800 text-white"}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : saved ? "Saved!" : "Save Changes"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function AdminLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(() => !getStoredToken());

  const [profile, setProfile] = useState<{ name: string; email: string; avatarUrl: string; role: string }>(() => {
    const stored = getStoredAdmin();
    return {
      name: stored ? `${stored.first_name || ""} ${stored.last_name || ""}`.trim() || stored.studio_name || stored.email || "" : "",
      email: stored?.email || "",
      avatarUrl: stored?.avatar_url || "",
      role: stored?.role || "",
    };
  });

  const isSuperAdmin = profile.role === "super_admin";

  // Static Creator / Studio Branding State
  const [branding, setBranding] = useState<{
    studioName: string;
    tagline: string;
    logoUrl: string;
  }>(() => {
    try {
      const raw = localStorage.getItem("admin_profile");
      if (raw) {
        const parsed = JSON.parse(raw);
        return {
          studioName: parsed.studio_name || "TalentSea",
          tagline: parsed.tagline || "",
          logoUrl: parsed.avatar_url || "",
        };
      }
    } catch {}
    return {
      studioName: "TalentSea",
      tagline: "",
      logoUrl: "",
    };
  });

  // Collapsible sidebar state (persisted in localStorage)
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem("sidebar_collapsed") === "true";
    } catch {
      return false;
    }
  });

  const toggleSidebar = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("sidebar_collapsed", String(next));
      } catch {}
      return next;
    });
  };

  const [tenants, setTenants] = useState<ApiTenant[]>([]);
  const [currentTenant, setCurrentTenant] = useState<ApiTenant | null>(null);

  useEffect(() => {
    if (!isSuperAdmin) return;
    let isMounted = true;
    getTenants()
      .then((list) => {
        if (!isMounted || !list || list.length === 0) return;
        setTenants(list);
        const savedTenantId = localStorage.getItem("current_tenant_id");
        const matched = (savedTenantId ? list.find((t) => String(t.id) === savedTenantId) : null) || list[0];
        setCurrentTenant(matched);
        localStorage.setItem("current_tenant_id", String(matched.id));
        localStorage.setItem("current_tenant_name", matched.name);
        setBranding((prev) => ({
          ...prev,
          studioName: matched.name,
          logoUrl: matched.logoUrl || prev.logoUrl,
          tagline: matched.tagline || prev.tagline,
        }));
      })
      .catch((err) => {
        console.warn("Could not load tenants for super admin:", err);
      });

    const handleTenantSwitched = (e: any) => {
      if (e.detail) {
        setCurrentTenant(e.detail);
        setBranding((prev) => ({
          ...prev,
          studioName: e.detail.name,
          logoUrl: e.detail.logoUrl || prev.logoUrl,
          tagline: e.detail.tagline || prev.tagline,
        }));
      }
    };
    window.addEventListener("tenant_switched", handleTenantSwitched);
    return () => {
      isMounted = false;
      window.removeEventListener("tenant_switched", handleTenantSwitched);
    };
  }, [isSuperAdmin]);

  const handleSwitchTenant = (tenant: ApiTenant) => {
    localStorage.setItem("current_tenant_id", String(tenant.id));
    localStorage.setItem("current_tenant_name", tenant.name);
    setCurrentTenant(tenant);
    setBranding((prev) => ({
      ...prev,
      studioName: tenant.name,
      logoUrl: tenant.logoUrl || "",
      tagline: tenant.tagline || "",
    }));
    window.dispatchEvent(new CustomEvent("tenant_switched", { detail: tenant }));
    window.location.reload();
  };

  // Fetch creator branding & listen for changes
  useEffect(() => {
    getCreatorBranding()
      .then((data) => {
        if (data) {
          const name = data.studioName || data.creatorName || "TalentSea";
          setBranding({
            studioName: name,
            tagline: data.tagline || "",
            logoUrl: data.logoUrl || "",
          });
        }
      })
      .catch((err) => {
        console.warn("Could not fetch branding for header:", err);
      });

    const handleBrandingUpdate = (e: any) => {
      if (e.detail) {
        setBranding((prev) => ({
          studioName: e.detail.studioName || e.detail.studio_name || prev.studioName,
          tagline: e.detail.tagline !== undefined ? e.detail.tagline : prev.tagline,
          logoUrl: e.detail.logoUrl || e.detail.logo_url || prev.logoUrl,
        }));
      }
    };
    window.addEventListener("branding_updated", handleBrandingUpdate);
    return () => window.removeEventListener("branding_updated", handleBrandingUpdate);
  }, []);

  // Rehydrate creator identity & verify active authentication session
  useEffect(() => {
    let isMounted = true;

    const applyAdminSession = (admin: any) => {
      setProfile({
        name: `${admin.first_name || ""} ${admin.last_name || ""}`.trim() || admin.studio_name || admin.email || "Admin",
        email: admin.email || "",
        avatarUrl: admin.avatar_url || "",
        role: admin.role || "",
      });
    };

    const verifySession = async () => {
      const storedToken = getStoredToken();
      if (!storedToken) {
        // No access token in storage: check if HttpOnly refresh cookie is present
        try {
          const refreshRes = await adminRefresh();
          if (!refreshRes?.access_token) {
            throw new Error("No token returned");
          }
          const admin = await adminGetMe();
          if (!isMounted) return;
          if (admin) {
            applyAdminSession(admin);
          }
          setIsCheckingAuth(false);
          return;
        } catch {
          if (!isMounted) return;
          clearStoredAuth();
          window.location.href = "/login";
          return;
        }
      }

      // Stored token exists: verify it via adminGetMe()
      try {
        const admin = await adminGetMe();
        if (!isMounted) return;
        if (admin) {
          applyAdminSession(admin);
        }
        setIsCheckingAuth(false);
      } catch (err: any) {
        // Token may have expired, attempt refresh
        try {
          await adminRefresh();
          const admin = await adminGetMe();
          if (!isMounted) return;
          if (admin) {
            applyAdminSession(admin);
          }
          setIsCheckingAuth(false);
        } catch (refreshErr: any) {
          if (!isMounted) return;
          // Check if failure is an explicit auth rejection (401/403)
          const msg = (refreshErr?.message || "").toLowerCase();
          const isExplicitAuthFailure =
            msg.includes("401") ||
            msg.includes("403") ||
            msg.includes("unauthorized") ||
            msg.includes("invalid token") ||
            msg.includes("credentials");

          if (isExplicitAuthFailure) {
            clearStoredAuth();
            window.location.href = "/login";
          } else {
            // Server might be sleeping (cold start), 502/504, or network hiccup.
            // Do NOT kick the user out! Keep cached credentials and stop blocking spinner.
            console.warn("Session re-verification encountered server delay/error:", refreshErr);
            setIsCheckingAuth(false);
          }
        }
      }
    };

    verifySession();

    return () => {
      isMounted = false;
    };
  }, [navigate]);

  // Synchronous route access check for super admin
  useEffect(() => {
    if (location.pathname.startsWith("/super-admin") && profile.role && profile.role !== "super_admin") {
      toast.error("Access Denied.");
      navigate("/", { replace: true });
    }
  }, [location.pathname, profile.role, navigate]);

  const handleLogout = async () => {
    try {
      await adminLogout();
      toast.success("Signed out successfully.");
    } catch {
      toast.error("Something went wrong while signing out.");
    } finally {
      navigate("/login", { replace: true });
    }
  };

  const NavLinks = ({ onLinkClick }: { onLinkClick?: () => void }) => {
    const navItems = isSuperAdmin
      ? [...navigation, { name: "Super Admin Center", path: "/super-admin", icon: ShieldCheck }]
      : navigation;

    return (
      <nav className={`space-y-1.5 ${isCollapsed ? "p-2" : "p-3"} flex-1 overflow-y-auto`}>
        {navItems.map((item) => {
          const isActive =
            location.pathname === item.path ||
            (item.path !== "/" && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.path}
              to={item.path}
              onClick={onLinkClick}
              title={item.name}
              className={`flex items-center rounded-xl text-sm font-semibold transition-all duration-150 ${
                isCollapsed
                  ? "justify-center p-3"
                  : "gap-3 px-3.5 py-2.5"
              } ${
                isActive
                  ? "bg-slate-900 text-white shadow-xs"
                  : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
              }`}
            >
              <item.icon className={`h-5 w-5 shrink-0 ${isActive ? "text-white" : "text-slate-500"}`} />
              {!isCollapsed && <span className="truncate">{item.name}</span>}
            </Link>
          );
        })}
      </nav>
    );
  };

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#F8F9FB] text-slate-900">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-slate-900 flex items-center justify-center shadow-sm">
            <span className="font-bold text-white text-xl">T</span>
          </div>
          <div className="flex items-center gap-2.5 text-slate-500 text-sm font-medium">
            <Loader2 className="h-4 w-4 animate-spin text-slate-900" />
            <span>Verifying session...</span>
          </div>
        </div>
      </div>
    );
  }



  return (
    <div className="min-h-screen bg-[#F8F9FB] text-slate-900 selection:bg-slate-900 selection:text-white">
      <ProfileDialog open={profileOpen} onClose={() => setProfileOpen(false)} />

      {/* Desktop sidebar */}
      <aside
        className={`fixed left-0 top-0 z-40 h-screen border-r border-slate-200 bg-white hidden lg:flex flex-col shadow-2xs transition-all duration-300 ease-in-out ${
          isCollapsed ? "w-20" : "w-64"
        }`}
      >
        <div
          className={`flex h-16 items-center border-b border-slate-200 ${
            isCollapsed ? "justify-center px-2" : "justify-between px-3"
          }`}
        >
          {isCollapsed ? (
            /* Collapsed state: Hover icon shows slider simple and "Open menu" tooltip at the side */
            <div className="relative group flex items-center justify-center">
              <button
                type="button"
                onClick={toggleSidebar}
                className="h-10 w-10 rounded-full flex items-center justify-center transition-colors relative overflow-hidden group/btn cursor-pointer"
                style={{ borderRadius: "50%" }}
                aria-label="Open menu"
              >
                {/* Normal state: Studio Logo / Initials */}
                <div
                  className="h-full w-full rounded-full bg-slate-900 flex items-center justify-center text-white font-bold shadow-xs transition-opacity duration-150 group-hover/btn:opacity-0 overflow-hidden"
                  style={{ borderRadius: "50%" }}
                >
                  {branding.logoUrl ? (
                    <img
                      src={branding.logoUrl}
                      alt={branding.studioName}
                      className="h-full w-full object-cover rounded-full"
                      style={{ borderRadius: "50%" }}
                    />
                  ) : (
                    <span className="font-bold text-white text-sm">
                      {(branding.studioName || "T").slice(0, 2).toUpperCase()}
                    </span>
                  )}
                </div>

                {/* Hover state: Slider Simple Icon (PanelLeftOpen) - Simple, no border highlight */}
                <div
                  className="absolute inset-0 flex items-center justify-center rounded-full bg-slate-100 text-slate-700 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-150"
                  style={{ borderRadius: "50%" }}
                >
                  <PanelLeftOpen className="h-5 w-5" />
                </div>
              </button>

              {/* Floating tooltip message at the side: "Open menu" like Gemini */}
              <div className="absolute left-full ml-3 top-1/2 -translate-y-1/2 px-2.5 py-1.5 bg-slate-900 text-white text-xs font-medium rounded-lg shadow-xl whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-all duration-150 z-50 flex items-center">
                <span>Open menu</span>
                <div className="absolute -left-1 top-1/2 -translate-y-1/2 border-y-4 border-y-transparent border-r-4 border-r-slate-900" />
              </div>
            </div>
          ) : (
            /* Expanded state: Static Studio Branding + Inner Close Button */
            <>
              {isSuperAdmin ? (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <button
                      type="button"
                      className="flex items-center gap-2.5 flex-1 overflow-hidden min-w-0 select-none text-left p-1 -m-1 rounded-xl hover:bg-slate-100/80 transition-colors group cursor-pointer border border-transparent hover:border-slate-200"
                    >
                      <div
                        className="h-10 w-10 rounded-full bg-slate-900 flex items-center justify-center text-white font-bold shadow-xs shrink-0 overflow-hidden"
                        style={{ borderRadius: "50%" }}
                      >
                        {branding.logoUrl ? (
                          <img
                            src={branding.logoUrl}
                            alt={branding.studioName}
                            className="h-full w-full object-cover rounded-full"
                            style={{ borderRadius: "50%" }}
                          />
                        ) : (
                          <span className="font-bold text-white text-base">
                            {(branding.studioName || "T").slice(0, 2).toUpperCase()}
                          </span>
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1">
                          <span className="font-bold text-base text-slate-900 tracking-tight truncate block leading-tight">
                            {branding.studioName || "TalentSea"}
                          </span>
                          <ChevronsUpDown className="h-4 w-4 text-slate-400 shrink-0 group-hover:text-slate-700" />
                        </div>
                        <span className="text-[10px] font-semibold text-purple-600 uppercase tracking-wider block leading-none mt-0.5">
                          Switch Tenant
                        </span>
                      </div>
                    </button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-64 p-2 bg-white border border-slate-200 rounded-2xl shadow-xl z-50">
                    <DropdownMenuLabel className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1.5 flex items-center justify-between">
                      <span>Platform Tenants</span>
                      <span className="bg-purple-100 text-purple-700 text-[10px] px-1.5 py-0.5 rounded-md font-bold">
                        {tenants.length} Studios
                      </span>
                    </DropdownMenuLabel>
                    <div className="max-h-60 overflow-y-auto space-y-1 py-1">
                      {tenants.map((t) => {
                        const isSelected = String(currentTenant?.id) === String(t.id) || branding.studioName === t.name;
                        return (
                          <DropdownMenuItem
                            key={t.id}
                            onClick={() => handleSwitchTenant(t)}
                            className={`flex items-center justify-between p-2 rounded-xl text-xs font-medium cursor-pointer transition-colors ${
                              isSelected ? "bg-slate-100 font-bold text-slate-900" : "hover:bg-slate-50 text-slate-700"
                            }`}
                          >
                            <div className="flex items-center gap-2.5 min-w-0">
                              <div className="h-7 w-7 rounded-lg bg-slate-900 text-white flex items-center justify-center text-xs font-bold shrink-0">
                                {t.name.charAt(0).toUpperCase()}
                              </div>
                              <div className="min-w-0 truncate">
                                <p className="truncate font-semibold">{t.name}</p>
                                <p className="text-[10px] text-slate-400 font-mono truncate">{t.slug}</p>
                              </div>
                            </div>
                            {isSelected && <Check className="h-4 w-4 text-emerald-600 shrink-0 ml-2" />}
                          </DropdownMenuItem>
                        );
                      })}
                      {tenants.length === 0 && (
                        <div className="p-3 text-center text-xs text-slate-400">Loading tenants...</div>
                      )}
                    </div>
                    <DropdownMenuSeparator className="my-1 bg-slate-100" />
                    <DropdownMenuItem
                      onClick={() => navigate("/super-admin")}
                      className="flex items-center gap-2 p-2 rounded-xl text-xs font-semibold text-slate-900 hover:bg-slate-50 cursor-pointer"
                    >
                      <ShieldCheck className="h-4 w-4 text-purple-600" />
                      Open Super Admin Center
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              ) : (
                <div className="flex items-center gap-3 flex-1 overflow-hidden min-w-0 select-none">
                  <div
                    className="h-10 w-10 rounded-full bg-slate-900 flex items-center justify-center text-white font-bold shadow-xs shrink-0 overflow-hidden"
                    style={{ borderRadius: "50%" }}
                  >
                    {branding.logoUrl ? (
                      <img
                        src={branding.logoUrl}
                        alt={branding.studioName}
                        className="h-full w-full object-cover rounded-full"
                        style={{ borderRadius: "50%" }}
                      />
                    ) : (
                      <span className="font-bold text-white text-base">
                        {(branding.studioName || "T").slice(0, 2).toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <span className="font-bold text-base text-slate-900 tracking-tight truncate block leading-tight">
                      {branding.studioName || "TalentSea"}
                    </span>
                  </div>
                </div>
              )}

              {/* Inner Close Button with tooltip */}
              <div className="relative group/close shrink-0">
                <button
                  type="button"
                  onClick={toggleSidebar}
                  aria-label="Close menu"
                  className="p-1.5 rounded-xl text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition-colors shrink-0 ml-1 cursor-pointer"
                >
                  <PanelLeftClose className="h-5 w-5" />
                </button>
                <div className="absolute right-0 top-full mt-1 px-2 py-1 bg-slate-900 text-white text-[11px] font-medium rounded-md shadow-md whitespace-nowrap opacity-0 group-hover/close:opacity-100 pointer-events-none transition-opacity duration-150 z-50">
                  <span>Close menu</span>
                </div>
              </div>
            </>
          )}
        </div>

        <NavLinks />
      </aside>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={() => setSidebarOpen(false)}>
          <aside className="fixed left-0 top-0 h-screen w-64 border-r border-slate-200 bg-white shadow-xl flex flex-col"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex h-16 items-center border-b border-slate-200 px-6">
              {/* Static Studio Branding on Mobile */}
              <div className="flex items-center gap-3 select-none min-w-0">
                <div
                  className="h-10 w-10 rounded-full bg-slate-900 flex items-center justify-center text-white font-bold shadow-xs shrink-0 overflow-hidden"
                  style={{ borderRadius: "50%" }}
                >
                  {branding.logoUrl ? (
                    <img
                      src={branding.logoUrl}
                      alt={branding.studioName}
                      className="h-full w-full object-cover rounded-full"
                      style={{ borderRadius: "50%" }}
                    />
                  ) : (
                    <span className="font-bold text-white text-base">
                      {(branding.studioName || "T").slice(0, 2).toUpperCase()}
                    </span>
                  )}
                </div>
                <div className="min-w-0 flex items-center shrink-1">
                  <span className="font-bold text-base text-slate-900 tracking-tight truncate">
                    {branding.studioName || "TalentSea"}
                  </span>
                </div>
              </div>
            </div>
            <NavLinks onLinkClick={() => setSidebarOpen(false)} />
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className={`transition-all duration-300 ease-in-out ${isCollapsed ? "lg:pl-20" : "lg:pl-64"}`}>
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-slate-200/80 bg-white/80 backdrop-blur-md pl-4 lg:pl-6 pr-3 sm:pr-4 shadow-2xs">
          <Button variant="ghost" size="icon" className="lg:hidden text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl" onClick={() => setSidebarOpen(true)}>
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex flex-1 items-center gap-4">
            <div className="relative max-w-md flex-1">
              <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input type="search" placeholder="Search videos, subscribers, analytics..." className="pl-10 bg-slate-50 text-slate-900 placeholder:text-slate-400 border border-slate-200 focus:bg-white focus:border-slate-900 rounded-xl h-10 text-sm" />
            </div>
          </div>

          <div className="flex items-center gap-2.5 ml-auto">
            <Button variant="ghost" size="icon" className="relative text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl h-10 w-10 shrink-0">
              <Bell className="h-5 w-5" />
              <span className="absolute right-2.5 top-2.5 h-2 w-2 rounded-full bg-rose-500" />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="gap-3 bg-white text-slate-900 hover:bg-slate-50 border border-slate-800 rounded-full pl-1 pr-4.5 py-1 shadow-xs h-[42px] transition-all cursor-pointer"
                  style={{ borderRadius: "9999px" }}
                >
                  <Avatar
                    className="h-[34px] w-[34px] rounded-full shrink-0 overflow-hidden"
                    style={{ borderRadius: "50%" }}
                  >
                    <AvatarImage
                      src={profile.avatarUrl}
                      className="rounded-full object-cover"
                      style={{ borderRadius: "50%" }}
                    />
                    <AvatarFallback
                      className="bg-slate-900 text-white text-xs font-bold rounded-full"
                      style={{ borderRadius: "50%" }}
                    >
                      {(profile.name || "TS").slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden md:inline text-xs font-semibold text-slate-900 whitespace-nowrap">{profile.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-white border-slate-200 text-slate-800 shadow-xl rounded-xl">
                <DropdownMenuLabel>
                  <div>
                    <p className="font-semibold text-slate-900">{profile.name}</p>
                    <p className="text-xs text-slate-500 font-normal">{profile.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-slate-100" />
                <DropdownMenuItem onClick={() => setProfileOpen(true)} className="hover:bg-slate-50 focus:bg-slate-50 cursor-pointer text-slate-700">
                  <User className="mr-2 h-4 w-4 text-slate-500" />Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/settings")} className="hover:bg-slate-50 focus:bg-slate-50 cursor-pointer text-slate-700">
                  <Settings className="mr-2 h-4 w-4 text-slate-500" />Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-slate-100" />
                <DropdownMenuItem className="text-rose-600 hover:bg-rose-50 focus:bg-rose-50 cursor-pointer" onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4 text-rose-500" />Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="p-6 md:p-8">
          <Outlet />
        </main>
        <ApiResponseMonitor />
      </div>
    </div>
  );
}
