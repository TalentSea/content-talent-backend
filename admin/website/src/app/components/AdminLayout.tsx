import { Outlet, Link, useLocation, useNavigate } from "react-router";
import {
  LayoutDashboard, Video, Users, CreditCard, BarChart3, DollarSign,
  MessageSquare, Palette, FolderTree, Settings, Menu, Bell,
  Search, User, LogOut, Camera, Mail, Phone, MapPin, Loader2,
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
import ApiResponseMonitor from "./ApiResponseMonitor";
import { getCreatorProfile, updateCreatorProfile, getDashboardStats } from "../services/apiService";

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
      <DialogContent className="max-w-lg bg-slate-900 border border-slate-800 text-slate-100">
        <DialogHeader>
          <DialogTitle className="text-white">My Profile</DialogTitle>
          <DialogDescription className="text-slate-400">Manage your personal information and studio profile</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
            <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
            <p className="text-sm">Loading profile...</p>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Avatar */}
            <div className="flex items-center gap-4">
              <div className="relative">
                {avatarUrl ? (
                  <img src={avatarUrl} alt={name} className="h-20 w-20 rounded-full object-cover border border-purple-500/40" />
                ) : (
                  <div className="h-20 w-20 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white text-2xl font-bold">
                    {(name || "C").charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div>
                <p className="font-semibold text-slate-100">{name || "Creator"}</p>
                <p className="text-sm text-slate-400">{email || "admin@talentsea.io"}</p>
              </div>
            </div>

            {/* Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-300 text-xs"><User className="h-3.5 w-3.5 text-purple-400" />Display Name</Label>
                <Input value={name} onChange={(e) => setName(e.target.value)} className="bg-slate-950 border-slate-800 text-slate-100" />
              </div>
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-300 text-xs"><Mail className="h-3.5 w-3.5 text-purple-400" />Email</Label>
                <Input type="email" value={email} disabled className="bg-slate-950/60 border-slate-800 text-slate-400 cursor-not-allowed" />
              </div>
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-300 text-xs"><Phone className="h-3.5 w-3.5 text-purple-400" />Phone</Label>
                <Input value={phone} onChange={(e) => setPhone(e.target.value)} className="bg-slate-950 border-slate-800 text-slate-100" />
              </div>
              <div>
                <Label className="flex items-center gap-1.5 mb-1 text-slate-300 text-xs"><MapPin className="h-3.5 w-3.5 text-purple-400" />Location</Label>
                <Input value={location} onChange={(e) => setLocation(e.target.value)} className="bg-slate-950 border-slate-800 text-slate-100" />
              </div>
            </div>
            <div>
              <Label className="mb-1 block text-slate-300 text-xs">Bio</Label>
              <textarea
                className="w-full border border-slate-800 rounded-lg p-2.5 text-sm text-slate-100 bg-slate-950 resize-none outline-none focus:ring-2 focus:ring-purple-600/20"
                rows={3}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
              />
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-3 bg-slate-950 border border-slate-800 rounded-lg p-3 text-center">
              {[
                { label: "Videos", value: stats.videos.toLocaleString() },
                { label: "Subscribers", value: stats.subscribers.toLocaleString() },
                { label: "Total Views", value: stats.views.toLocaleString() },
              ].map((s) => (
                <div key={s.label}>
                  <div className="font-bold text-purple-400">{s.value}</div>
                  <div className="text-xs text-slate-400">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onClose} className="border-slate-800 bg-slate-800 text-slate-300 hover:bg-slate-700">Cancel</Button>
          <Button onClick={handleSave} disabled={saving || loading} className={saved ? "bg-emerald-600 hover:bg-emerald-500 text-white" : "bg-purple-600 hover:bg-purple-500 text-white"}>
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
  const [profile, setProfile] = useState<{ name: string; email: string; avatarUrl: string }>({
    name: "Creator Studio",
    email: "admin@talentsea.io",
    avatarUrl: "",
  });

  useEffect(() => {
    getCreatorProfile()
      .then((p) => {
        if (p) {
          setProfile({
            name: p.fullName || `${p.firstName || ""} ${p.lastName || ""}`.trim() || "Creator Studio",
            email: p.email || "admin@talentsea.io",
            avatarUrl: p.avatarUrl || "",
          });
        }
      })
      .catch(() => {});
  }, [profileOpen]);

  const NavLinks = ({ onLinkClick }: { onLinkClick?: () => void }) => (
    <nav className="space-y-1.5 p-4">
      {navigation.map((item) => {
        const isActive =
          location.pathname === item.path ||
          (item.path !== "/" && location.pathname.startsWith(item.path));
        return (
          <Link
            key={item.path}
            to={item.path}
            onClick={onLinkClick}
            className={`flex items-center gap-3.5 rounded-xl px-4 py-2.5 text-sm font-medium transition-all duration-200 ${
              isActive
                ? "bg-gradient-to-r from-purple-600/30 to-blue-600/20 text-purple-300 border border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.15)] font-semibold"
                : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/50"
            }`}
          >
            <item.icon className={`h-5 w-5 ${isActive ? "text-purple-400" : "text-slate-400"}`} />
            {item.name}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 selection:bg-purple-500/30">
      <ProfileDialog open={profileOpen} onClose={() => setProfileOpen(false)} />

      {/* Desktop sidebar */}
      <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-slate-800/80 bg-slate-950/90 backdrop-blur-xl hidden lg:block shadow-2xl">
        <div className="flex h-16 items-center border-b border-slate-800/80 px-6">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-purple-500 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-[0_0_20px_rgba(168,85,247,0.4)]">
              <span className="font-bold text-white text-lg">T</span>
            </div>
            <div>
              <span className="font-bold text-lg text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-100 to-purple-300">
                TalentSea
              </span>
              <span className="text-[10px] block font-mono text-purple-400 -mt-1 tracking-wider uppercase">Studio Admin</span>
            </div>
          </div>
        </div>
        <NavLinks />
      </aside>

      {/* Mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}>
          <aside className="fixed left-0 top-0 h-screen w-64 border-r border-slate-800 bg-slate-950"
            onClick={(e) => e.stopPropagation()}>
            <div className="flex h-16 items-center border-b border-slate-800 px-6">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-purple-500 to-cyan-400 flex items-center justify-center">
                  <span className="font-bold text-white text-lg">T</span>
                </div>
                <span className="font-bold text-lg text-white">TalentSea Studio</span>
              </div>
            </div>
            <NavLinks onLinkClick={() => setSidebarOpen(false)} />
          </aside>
        </div>
      )}

      {/* Main content */}
      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl px-6 shadow-lg">
          <Button variant="ghost" size="icon" className="lg:hidden text-slate-300 hover:text-white hover:bg-slate-800" onClick={() => setSidebarOpen(true)}>
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex flex-1 items-center gap-4">
            <div className="relative max-w-md flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <Input type="search" placeholder="Search videos, subscribers, analytics..." className="pl-9 bg-slate-900/90 text-slate-100 placeholder:text-slate-500 border border-slate-800 focus:border-purple-500/50 rounded-xl" />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="relative text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 rounded-xl">
              <Bell className="h-5 w-5" />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="gap-2.5 text-slate-200 hover:bg-slate-800/60 border border-slate-800/80 rounded-xl px-3 py-1.5">
                  <Avatar className="h-8 w-8 ring-2 ring-purple-500/40">
                    <AvatarImage src={profile.avatarUrl} />
                    <AvatarFallback className="bg-gradient-to-br from-purple-500 to-cyan-500 text-white text-xs font-bold">
                      {(profile.name || "TS").slice(0, 2).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden md:inline text-sm font-medium">{profile.name}</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-slate-900 border-slate-800 text-slate-200 shadow-2xl">
                <DropdownMenuLabel>
                  <div>
                    <p className="font-semibold text-white">{profile.name}</p>
                    <p className="text-xs text-slate-400 font-normal">{profile.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-slate-800" />
                <DropdownMenuItem onClick={() => setProfileOpen(true)} className="hover:bg-slate-800 focus:bg-slate-800 cursor-pointer">
                  <User className="mr-2 h-4 w-4 text-purple-400" />Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/settings")} className="hover:bg-slate-800 focus:bg-slate-800 cursor-pointer">
                  <Settings className="mr-2 h-4 w-4 text-purple-400" />Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-slate-800" />
                <DropdownMenuItem className="text-red-400 hover:bg-slate-800 focus:bg-slate-800 cursor-pointer" onClick={() => navigate("/login")}>
                  <LogOut className="mr-2 h-4 w-4" />Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="p-6">
          <Outlet />
        </main>
        <ApiResponseMonitor />
      </div>
    </div>
  );
}
