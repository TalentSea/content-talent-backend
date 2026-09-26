import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Switch } from "../components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  User, Lock, Bell, CreditCard, Globe, Shield, Save, Loader2, Upload, Check,
  Building2, AlertCircle, CheckCircle2, UserCheck, UserPlus, Eye, EyeOff, Power, RefreshCw
} from "lucide-react";
import { Badge } from "../components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import { Separator } from "../components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../components/ui/dialog";
import {
  getCreatorProfile,
  updateCreatorProfile,
  uploadAvatarPhoto,
  getPayoutSettings,
  updatePayoutSettings,
  getTenantUsers,
  createTenantUser,
  toggleTenantUserActive,
  changeAdminPassword,
  getTenants,
  getStoredAdmin,
  ApiProfile,
  ApiPayoutProfile,
  TenantUser,
  ApiTenant,
} from "../services/apiService";

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [savingSection, setSavingSection] = useState<string | null>(null);
  const [savedSection, setSavedSection] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // In-Session Password Change State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPwd, setShowCurrentPwd] = useState(false);
  const [showNewPwd, setShowNewPwd] = useState(false);
  const [showConfirmPwd, setShowConfirmPwd] = useState(false);

  // Form Fields
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [bio, setBio] = useState("");
  const [website, setWebsite] = useState("");
  const [phone, setPhone] = useState("");
  const [location, setLocation] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [twitter, setTwitter] = useState("");
  const [youtube, setYoutube] = useState("");
  const [instagram, setInstagram] = useState("");

  // Bank Payout Account Fields
  const [bankProfile, setBankProfile] = useState<ApiPayoutProfile | null>(null);
  const [accountHolderName, setAccountHolderName] = useState("");
  const [accountNumber, setAccountNumber] = useState("");
  const [ifscCode, setIfscCode] = useState("");
  const [bankError, setBankError] = useState<string | null>(null);
  const [bankSuccess, setBankSuccess] = useState<string | null>(null);

  // Tenant Admin Users State
  const [tenantUsers, setTenantUsers] = useState<TenantUser[]>([]);
  const [loadingTenantUsers, setLoadingTenantUsers] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserFirstName, setNewUserFirstName] = useState("");
  const [newUserLastName, setNewUserLastName] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [isAddUserOpen, setIsAddUserOpen] = useState(false);
  const [addingUser, setAddingUser] = useState(false);
  const [togglingUserId, setTogglingUserId] = useState<number | null>(null);

  const loadTenantUsers = async () => {
    setLoadingTenantUsers(true);
    try {
      const users = await getTenantUsers();
      setTenantUsers(users);
    } catch (err: any) {
      console.warn("Could not load tenant users:", err);
    } finally {
      setLoadingTenantUsers(false);
    }
  };

  const handleAddTenantUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserEmail.trim() || !newUserPassword.trim() || !newUserFirstName.trim() || !newUserLastName.trim()) {
      toast.error("Please provide email, password, first name, and last name.");
      return;
    }
    setAddingUser(true);
    try {
      const created = await createTenantUser({
        email: newUserEmail.trim(),
        password: newUserPassword,
        first_name: newUserFirstName.trim(),
        last_name: newUserLastName.trim(),
      });
      setTenantUsers((prev) => [created, ...prev]);
      setNewUserEmail("");
      setNewUserPassword("");
      setNewUserFirstName("");
      setNewUserLastName("");
      toast.success(`User ${created.email} added successfully.`);
      setIsAddUserOpen(false);
    } catch (err: any) {
      toast.error(err?.message || "Failed to create tenant user.");
    } finally {
      setAddingUser(false);
    }
  };

  const handleToggleUserActive = async (user: TenantUser) => {
    setTogglingUserId(user.id);
    const currentActive = user.is_active ?? user.isActive ?? true;
    try {
      const res = await toggleTenantUserActive(user.id, currentActive);
      setTenantUsers((prev) =>
        prev.map((u) =>
          u.id === user.id ? { ...u, is_active: res.is_active, isActive: res.is_active } : u
        )
      );
      const actionText = res.is_active ? "activated" : "deactivated";
      toast.success(`User ${user.email} ${actionText} successfully.`);
    } catch (err: any) {
      toast.error(err?.message || "Failed to update user status.");
    } finally {
      setTogglingUserId(null);
    }
  };

  const storedAdmin = getStoredAdmin();
  const isSuperAdmin = storedAdmin?.role === "super_admin";

  // Load Profile, Payout Settings, and Tenant Users from API
  const loadSettingsData = async () => {
    setLoading(true);
    try {
      const [profile, payout, users] = await Promise.all([
        getCreatorProfile().catch((err) => {
          console.warn("Failed to load creator profile from API", err);
          return null;
        }),
        getPayoutSettings().catch((err) => {
          console.warn("Failed to load payout settings from API", err);
          return null;
        }),
        getTenantUsers().catch((err) => {
          console.warn("Failed to load tenant users from API", err);
          return [];
        }),
      ]);

      if (Array.isArray(users)) {
        setTenantUsers(users);
      }

      if (isSuperAdmin) {
        // While in superadmin mode, display active tenant admin details in Settings profile
        let tenantInfo: ApiTenant | null = null;
        try {
          const tenantList = await getTenants();
          const currentId = localStorage.getItem("current_tenant_id");
          tenantInfo = (currentId ? tenantList.find((t) => String(t.id) === currentId) : null) || tenantList[0] || null;
        } catch (e) {
          console.warn("Could not load tenant info for super admin:", e);
        }

        const tenantAdmin = Array.isArray(users) && users.length > 0 ? users[0] : null;
        if (tenantAdmin) {
          setFirstName(tenantAdmin.first_name || "");
          setLastName(tenantAdmin.last_name || "");
          setEmail(tenantAdmin.email || "");
          setPhone((tenantAdmin as any).phone || "");
          setAvatarUrl(tenantAdmin.avatar_url || tenantAdmin.avatarUrl || "");
          setBio("");
          setWebsite("");
          setLocation("");
          setTwitter("");
          setYoutube("");
          setInstagram("");
        } else if (tenantInfo) {
          setFirstName(tenantInfo.name || "Studio");
          setLastName("Admin");
          setEmail(tenantInfo.slug ? `admin@${tenantInfo.slug}.com` : "");
          setPhone("");
          setAvatarUrl("");
          setBio("");
          setWebsite("");
          setLocation("");
          setTwitter("");
          setYoutube("");
          setInstagram("");
        } else {
          setFirstName("");
          setLastName("");
          setEmail("");
          setPhone("");
          setAvatarUrl("");
          setBio("");
          setWebsite("");
          setLocation("");
          setTwitter("");
          setYoutube("");
          setInstagram("");
        }
      } else {
        if (profile) {
          if (profile.firstName) setFirstName(profile.firstName);
          if (profile.lastName) setLastName(profile.lastName);
          if (profile.email) setEmail(profile.email);
          if (profile.bio !== undefined) setBio(profile.bio);
          if (profile.website !== undefined) setWebsite(profile.website);
          if (profile.phone !== undefined) setPhone(profile.phone);
          if (profile.location !== undefined) setLocation(profile.location);
          if (profile.avatarUrl) setAvatarUrl(profile.avatarUrl);
          if (profile.socialLinks) {
            setTwitter(profile.socialLinks.twitter || "");
            setYoutube(profile.socialLinks.youtube || "");
            setInstagram(profile.socialLinks.instagram || "");
          }
        }
      }

      if (payout) {
        setBankProfile(payout);
        if (payout.account_holder_name) setAccountHolderName(payout.account_holder_name);
        if (payout.ifsc_code) setIfscCode(payout.ifsc_code);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettingsData();

    const handleTenantSwitched = () => {
      loadSettingsData();
    };
    window.addEventListener("tenant_switched", handleTenantSwitched);
    return () => window.removeEventListener("tenant_switched", handleTenantSwitched);
  }, []);

  // Save Section Changes Handler
  const handleSaveSection = async (sectionKey: string) => {
    setSavingSection(sectionKey);
    setBankError(null);
    setBankSuccess(null);
    try {
      if (sectionKey === "profile" || sectionKey === "social") {
        await updateCreatorProfile({
          first_name: firstName,
          last_name: lastName,
          bio,
          website,
          phone,
          location,
          social_links: {
            twitter,
            youtube,
            instagram,
          },
        });
        toast.success("Profile settings saved successfully!");
      } else if (sectionKey === "billing") {
        if (!accountHolderName.trim() || accountHolderName.trim().length < 3) {
          throw new Error("Account holder name must be at least 3 characters.");
        }
        if (!accountNumber.trim() || accountNumber.trim().length < 9) {
          throw new Error("Account number must be between 9 and 18 digits.");
        }
        const cleanIfsc = ifscCode.trim().toUpperCase();
        const ifscRegex = /^[A-Z]{4}0[A-Z0-9]{6}$/;
        if (!ifscRegex.test(cleanIfsc)) {
          throw new Error("Invalid Indian IFSC format (e.g. HDFC0000128).");
        }

        const updated = await updatePayoutSettings({
          account_holder_name: accountHolderName.trim(),
          account_number: accountNumber.trim(),
          ifsc_code: cleanIfsc,
        });
        setBankProfile(updated);
        setAccountNumber("");
        const msg = `Bank details registered! Resolved Bank: ${updated.bank_name || "Verified"}`;
        setBankSuccess(msg);
        toast.success(msg);
      } else if (sectionKey === "password") {
        if (!currentPassword) {
          throw new Error("Please enter your current password.");
        }
        if (!newPassword || newPassword.length < 8) {
          throw new Error("New password must be at least 8 characters long.");
        }
        if (newPassword === currentPassword) {
          throw new Error("New password cannot be identical to your current password.");
        }
        if (newPassword !== confirmPassword) {
          throw new Error("New password and confirm password do not match.");
        }

        await changeAdminPassword({
          current_password: currentPassword,
          new_password: newPassword,
        });
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        toast.success("Password changed successfully!");
      } else {
        // Minor async delay for other setting section triggers
        await new Promise((resolve) => setTimeout(resolve, 300));
        toast.success(`${sectionKey.charAt(0).toUpperCase() + sectionKey.slice(1)} settings updated.`);
      }
      setSavedSection(sectionKey);
      setTimeout(() => {
        setSavedSection((prev) => (prev === sectionKey ? null : prev));
      }, 3000);
    } catch (err: any) {
      const errMsg = err?.message || `Failed to update ${sectionKey} settings.`;
      if (sectionKey === "billing") {
        setBankError(errMsg);
      }
      toast.error(errMsg);
      console.error(`Failed to update ${sectionKey} settings`, err);
    } finally {
      setSavingSection(null);
    }
  };

  // Helper renderer for modular Section Save Buttons
  const renderSaveButton = (sectionKey: string, customLabel = "Save Changes") => {
    const isSaving = savingSection === sectionKey;
    const isSaved = savedSection === sectionKey;

    return (
      <Button
        onClick={() => handleSaveSection(sectionKey)}
        disabled={isSaving || loading}
        size="sm"
        className={`gap-1.5 font-semibold text-xs rounded-xl shadow-xs transition-all duration-200 ${
          isSaved
            ? "bg-emerald-600 hover:bg-emerald-700 text-white"
            : "bg-slate-900 hover:bg-slate-800 text-white"
        }`}
      >
        {isSaving ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : isSaved ? (
          <Check className="h-3.5 w-3.5" />
        ) : (
          <Save className="h-3.5 w-3.5" />
        )}
        {isSaving ? "Saving..." : isSaved ? "Saved!" : customLabel}
      </Button>
    );
  };

  // Upload Avatar File
  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || !e.target.files[0]) return;
    const file = e.target.files[0];
    setUploadingAvatar(true);
    try {
      const res = await uploadAvatarPhoto(file);
      if (res.avatarUrl) {
        setAvatarUrl(res.avatarUrl);
        toast.success("Profile photo updated successfully!");
      }
    } catch (err: any) {
      toast.error(err?.message || "Failed to upload avatar photo.");
      console.error("Failed to upload avatar photo", err);
    } finally {
      setUploadingAvatar(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Hidden File Input for Avatar */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleAvatarChange}
        accept="image/png, image/jpeg, image/webp"
        className="hidden"
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Settings</h1>
          <p className="text-sm text-slate-500 mt-1">Manage your creator profile, credentials, and payout configurations.</p>
        </div>
      </div>

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList className="bg-slate-100 border border-slate-200/80 p-1 rounded-xl inline-flex w-full lg:w-auto overflow-x-auto gap-1">
          <TabsTrigger value="profile" className="gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
            <User className="h-4 w-4" />
            <span>Profile</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
            <Lock className="h-4 w-4" />
            <span>Security</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
            <Bell className="h-4 w-4" />
            <span>Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
            <Building2 className="h-4 w-4" />
            <span>Payouts</span>
          </TabsTrigger>

          <TabsTrigger value="advanced" className="gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all">
            <Shield className="h-4 w-4" />
            <span>Advanced</span>
          </TabsTrigger>
          <TabsTrigger value="admin" className="gap-2 data-[state=active]:bg-white data-[state=active]:text-slate-900 data-[state=active]:shadow-xs rounded-lg px-3 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-all cursor-pointer">
            <UserCheck className="h-4 w-4" />
            <span>Admin</span>
          </TabsTrigger>
        </TabsList>

        {/* Profile Settings */}
        <TabsContent value="profile" className="space-y-6">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b border-slate-100">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 tracking-tight">Profile Information</CardTitle>
              </div>
              {renderSaveButton("profile")}
            </CardHeader>
            <CardContent className="space-y-5 pt-5">
              {loading ? (
                <div className="flex items-center justify-center py-8 text-slate-400 gap-2">
                  <Loader2 className="h-5 w-5 animate-spin" /> Loading profile details...
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-6">
                    <div className="h-20 w-20 rounded-2xl bg-slate-900 text-white flex items-center justify-center text-2xl font-bold overflow-hidden relative shadow-xs">
                      {avatarUrl ? (
                        <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
                      ) : (
                        `${firstName ? firstName.charAt(0) : "C"}${lastName ? lastName.charAt(0) : "T"}`
                      )}
                    </div>
                    <div>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={uploadingAvatar}
                        onClick={() => fileInputRef.current?.click()}
                        className="gap-2 rounded-xl border-slate-200 hover:bg-slate-50 text-slate-700 shadow-xs text-sm font-semibold h-9 px-3"
                      >
                        {uploadingAvatar ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
                        {uploadingAvatar ? "Uploading..." : "Change Avatar"}
                      </Button>
                      <p className="text-xs text-slate-400 mt-1.5 font-normal">JPG, PNG or WEBP (Max 2MB)</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="first-name" className="text-sm font-semibold text-slate-800 block mb-1.5">First Name</Label>
                      <Input id="first-name" value={firstName} onChange={(e) => setFirstName(e.target.value)} className="rounded-xl border-slate-200" />
                    </div>
                    <div>
                      <Label htmlFor="last-name" className="text-sm font-semibold text-slate-800 block mb-1.5">Last Name</Label>
                      <Input id="last-name" value={lastName} onChange={(e) => setLastName(e.target.value)} className="rounded-xl border-slate-200" />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="email" className="text-sm font-semibold text-slate-800 block mb-1.5">Email Address <span className="text-xs text-slate-400 font-normal">(Read-only)</span></Label>
                    <Input id="email" type="email" value={email} disabled className="bg-slate-50 border-slate-200 text-slate-500 cursor-not-allowed rounded-xl" />
                  </div>
                  <div>
                    <Label htmlFor="bio" className="text-sm font-semibold text-slate-800 block mb-1.5">Bio</Label>
                    <Input id="bio" value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Tell your audience about your channel" className="rounded-xl border-slate-200" />
                  </div>
                  <div>
                    <Label htmlFor="website" className="text-sm font-semibold text-slate-800 block mb-1.5">Website</Label>
                    <Input id="website" value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://example.com" className="rounded-xl border-slate-200" />
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <Label htmlFor="phone" className="text-sm font-semibold text-slate-800 block mb-1.5">Phone Number</Label>
                      <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+1 (555) 000-0000" className="rounded-xl border-slate-200" />
                    </div>
                    <div>
                      <Label htmlFor="location" className="text-sm font-semibold text-slate-800 block mb-1.5">Location</Label>
                      <Input id="location" value={location} onChange={(e) => setLocation(e.target.value)} placeholder="City, Country" className="rounded-xl border-slate-200" />
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b border-slate-100">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 tracking-tight">Social Links</CardTitle>
              </div>
              {renderSaveButton("social")}
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <div>
                <Label htmlFor="twitter" className="text-sm font-semibold text-slate-800 block mb-1.5">Twitter / X</Label>
                <Input id="twitter" value={twitter} onChange={(e) => setTwitter(e.target.value)} placeholder="https://twitter.com/username" className="rounded-xl border-slate-200" />
              </div>
              <div>
                <Label htmlFor="youtube" className="text-sm font-semibold text-slate-800 block mb-1.5">YouTube</Label>
                <Input id="youtube" value={youtube} onChange={(e) => setYoutube(e.target.value)} placeholder="https://youtube.com/@username" className="rounded-xl border-slate-200" />
              </div>
              <div>
                <Label htmlFor="instagram" className="text-sm font-semibold text-slate-800 block mb-1.5">Instagram</Label>
                <Input id="instagram" value={instagram} onChange={(e) => setInstagram(e.target.value)} placeholder="https://instagram.com/username" className="rounded-xl border-slate-200" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-6">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b border-slate-100">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 tracking-tight">Change Password</CardTitle>
                <p className="text-xs text-slate-500 mt-1">
                  Ensure your account uses a strong password with at least 8 characters.
                </p>
              </div>
              {renderSaveButton("password", "Update Password")}
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <div>
                <Label htmlFor="current-password" className="text-sm font-semibold text-slate-800 block mb-1.5">
                  Current Password
                </Label>
                <div className="relative">
                  <Input
                    id="current-password"
                    type={showCurrentPwd ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                    className="rounded-xl border-slate-200 pr-10"
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrentPwd((prev) => !prev)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                  >
                    {showCurrentPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <Label htmlFor="new-password" className="text-sm font-semibold text-slate-800 block mb-1.5">
                  New Password
                </Label>
                <div className="relative">
                  <Input
                    id="new-password"
                    type={showNewPwd ? "text" : "password"}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="At least 8 characters (distinct from current)"
                    className="rounded-xl border-slate-200 pr-10"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewPwd((prev) => !prev)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                  >
                    {showNewPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <Label htmlFor="confirm-password" className="text-sm font-semibold text-slate-800 block mb-1.5">
                  Confirm New Password
                </Label>
                <div className="relative">
                  <Input
                    id="confirm-password"
                    type={showConfirmPwd ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Re-enter new password"
                    className="rounded-xl border-slate-200 pr-10"
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPwd((prev) => !prev)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                  >
                    {showConfirmPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>


        </TabsContent>

        {/* Notification Settings */}
        <TabsContent value="notifications" className="space-y-6">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b border-slate-100">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 tracking-tight">Email Notifications</CardTitle>
              </div>
              {renderSaveButton("notifications")}
            </CardHeader>
            <CardContent className="space-y-5 pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm text-slate-900">New Subscribers</div>
                  <div className="text-xs text-slate-500 mt-0.5">Get notified instantly when someone joins a paid tier</div>
                </div>
                <Switch defaultChecked />
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-sm text-slate-900">Comments & Engagement</div>
                  <div className="text-xs text-slate-500 mt-0.5">Get notified about new community discussions and replies</div>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Payout & Bank Account Settings */}
        <TabsContent value="billing" className="space-y-6">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b border-slate-100">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 tracking-tight">Bank Payout Account</CardTitle>
              </div>
              {renderSaveButton("billing", "Save Bank Details")}
            </CardHeader>
            <CardContent className="space-y-6 pt-5">
              {bankSuccess && (
                <div className="flex items-center gap-2 text-sm font-semibold text-emerald-800 bg-emerald-50 p-3.5 rounded-xl border border-emerald-200">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
                  <span>{bankSuccess}</span>
                </div>
              )}

              {bankError && (
                <div className="flex items-center gap-2 text-sm font-semibold text-red-800 bg-red-50 p-3.5 rounded-xl border border-red-200">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
                  <span>{bankError}</span>
                </div>
              )}

              {bankProfile?.is_configured && (
                <div className="border border-emerald-200 bg-emerald-50/50 rounded-2xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="h-11 w-11 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold shadow-xs shrink-0">
                      <Building2 className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-slate-900">
                          {bankProfile.bank_name || "Verified Commercial Bank"}
                        </span>
                        <Badge className="bg-emerald-100 text-emerald-800 border border-emerald-200 text-xs font-semibold">
                          Active & Linked
                        </Badge>
                      </div>
                      <div className="text-xs text-slate-600 mt-1">
                        Account: <span className="font-mono font-medium text-slate-900">{bankProfile.account_number_masked}</span> • IFSC: <span className="font-mono font-medium text-slate-900">{bankProfile.ifsc_code}</span>
                      </div>
                      <div className="text-xs text-slate-500 mt-0.5">
                        Beneficiary: {bankProfile.account_holder_name}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs md:text-right text-slate-500 font-medium">
                    Auto-disbursed on the 28th
                  </div>
                </div>
              )}

              <div className="space-y-4">
                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-700">
                  {bankProfile?.is_configured ? "Update Account Details" : "Register Payout Account"}
                </h4>
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <Label htmlFor="account-holder" className="text-sm font-semibold text-slate-800 block mb-1.5">Account Holder / Beneficiary Name</Label>
                    <Input
                      id="account-holder"
                      placeholder="e.g. TalentSea Media Ltd or John Doe"
                      value={accountHolderName}
                      onChange={(e) => setAccountHolderName(e.target.value)}
                      className="rounded-xl border-slate-200"
                    />
                  </div>
                  <div>
                    <Label htmlFor="ifsc-code" className="text-sm font-semibold text-slate-800 block mb-1.5">IFSC Code</Label>
                    <Input
                      id="ifsc-code"
                      placeholder="e.g. HDFC0000128"
                      maxLength={11}
                      value={ifscCode}
                      onChange={(e) => setIfscCode(e.target.value.toUpperCase())}
                      className="rounded-xl border-slate-200 font-mono uppercase"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="account-number" className="text-sm font-semibold text-slate-800 block mb-1.5">Bank Account Number</Label>
                  <Input
                    id="account-number"
                    type="password"
                    placeholder={bankProfile?.is_configured ? "Enter new number to update" : "9 to 18 digits account number"}
                    value={accountNumber}
                    onChange={(e) => setAccountNumber(e.target.value)}
                    className="rounded-xl border-slate-200 font-mono"
                  />
                </div>
              </div>

              <Separator />

              <div className="bg-slate-50 rounded-2xl p-4 border border-slate-200/80 space-y-2 text-xs text-slate-600">
                <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                  <Building2 className="h-4 w-4 text-slate-900" />
                  Net-30 Settlement Lifecycle & Schedule
                </div>
                <p>
                  • <strong className="text-slate-800">Accrual Period:</strong> IMA VAST impressions accrue from the 1st to the end of each calendar month.
                </p>
                <p>
                  • <strong className="text-slate-800">Audit & Reconciliation:</strong> Between the 1st and 20th of the following month, impressions undergo fraud and invalid-traffic scrubbing.
                </p>
                <p>
                  • <strong className="text-slate-800">Disbursement Date:</strong> Payouts are executed automatically on the <strong className="text-slate-800">28th of every month</strong> for accounts with total accrued earnings of at least <strong className="text-slate-800">₹500</strong>. Balances under ₹500 roll over into the next cycle.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Settings */}
        <TabsContent value="advanced" className="space-y-6">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4 border-b border-slate-100">
              <div>
                <CardTitle className="text-base font-bold text-slate-900 tracking-tight">Data & Privacy</CardTitle>
                <p className="text-xs text-slate-500 mt-0.5">Export data and audit platform privacy compliance</p>
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-5">
              <Button variant="outline" className="rounded-xl border-slate-200 hover:bg-slate-50 text-slate-700 shadow-xs text-xs font-semibold">
                Download My Data
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Admin - Tenant Users Management */}
        <TabsContent value="admin" className="space-y-6">          
          {/* Card: Tenant Users Roster */}
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="border-b border-slate-100 pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 tracking-tight">
                  Tenant Users
                </CardTitle>
                <p className="text-xs text-slate-500">
                  Users registered under this tenant workspace ({tenantUsers.length} total).
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={loadTenantUsers}
                  disabled={loadingTenantUsers}
                  className="rounded-xl border-slate-200 text-xs text-slate-700 hover:bg-slate-50 cursor-pointer h-9 px-3"
                >
                  <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loadingTenantUsers ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
                <Dialog open={isAddUserOpen} onOpenChange={setIsAddUserOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" className="bg-slate-900 text-white hover:bg-slate-800 rounded-xl text-xs font-semibold h-9 px-3.5 cursor-pointer">
                      <UserPlus className="h-3.5 w-3.5 mr-1.5" /> Add User
                    </Button>
                  </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Add New Admin User</DialogTitle>
                  </DialogHeader>
                  <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
                    <CardHeader className="border-b border-slate-100 pb-4">
                      <CardTitle className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                        <UserPlus className="h-5 w-5 text-slate-700" />
                        Add User to Tenant
                      </CardTitle>
                      <p className="text-xs text-slate-500">
                        Create a new user account with administrative access for this tenant.
                      </p>
                    </CardHeader>
                    <CardContent className="pt-5">
                      <form onSubmit={handleAddTenantUser} className="grid gap-4 md:grid-cols-2 items-end">
                        <div>
                          <Label className="text-xs font-semibold text-slate-700 block mb-1.5">
                            First Name
                          </Label>
                          <Input
                            type="text"
                            placeholder="John"
                            value={newUserFirstName}
                            onChange={(e) => setNewUserFirstName(e.target.value)}
                            className="rounded-xl border-slate-200 text-sm bg-white"
                            required
                          />
                        </div>

                        <div>
                          <Label className="text-xs font-semibold text-slate-700 block mb-1.5">
                            Last Name
                          </Label>
                          <Input
                            type="text"
                            placeholder="Doe"
                            value={newUserLastName}
                            onChange={(e) => setNewUserLastName(e.target.value)}
                            className="rounded-xl border-slate-200 text-sm bg-white"
                            required
                          />
                        </div>

                        <div>
                          <Label className="text-xs font-semibold text-slate-700 block mb-1.5">
                            User Email
                          </Label>
                          <Input
                            type="email"
                            placeholder="user@domain.com"
                            value={newUserEmail}
                            onChange={(e) => setNewUserEmail(e.target.value)}
                            className="rounded-xl border-slate-200 text-sm bg-white"
                            required
                          />
                        </div>

                        <div>
                          <Label className="text-xs font-semibold text-slate-700 block mb-1.5">
                            Password
                          </Label>
                          <div className="relative">
                            <Input
                              type={showNewPassword ? "text" : "password"}
                              placeholder="••••••••••••"
                              value={newUserPassword}
                              onChange={(e) => setNewUserPassword(e.target.value)}
                              className="rounded-xl border-slate-200 text-sm pr-10 bg-white"
                              required
                            />
                            <button
                              type="button"
                              onClick={() => setShowNewPassword(!showNewPassword)}
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 cursor-pointer"
                            >
                              {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                          </div>
                        </div>

                        <div className="md:col-span-2 flex justify-end">
                          <Button
                            type="submit"
                            disabled={addingUser}
                            className="bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-xl text-xs h-10 px-5 shadow-xs cursor-pointer"
                          >
                            {addingUser ? (
                              <Loader2 className="h-4 w-4 animate-spin mr-1.5" />
                            ) : (
                              <UserPlus className="h-4 w-4 mr-1.5" />
                            )}
                            Add User
                          </Button>
                        </div>
                      </form>
                    </CardContent>
                  </Card>
                </DialogContent>
              </Dialog>
            </div>
          </CardHeader>


            <CardContent className="pt-0 p-0">
              {loadingTenantUsers ? (
                <div className="py-12 flex flex-col items-center justify-center text-slate-400 gap-2">
                  <Loader2 className="h-6 w-6 animate-spin text-slate-900" />
                  <p className="text-xs">Loading tenant users...</p>
                </div>
              ) : tenantUsers.length === 0 ? (
                <div className="py-12 text-center text-slate-500 text-sm">
                  No users found for this tenant.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-sm">
                    <thead>
                      <tr className="border-b border-slate-100 text-slate-400 text-xs font-semibold bg-slate-50/50">
                        <th className="p-4 pl-6">User</th>
                        <th className="p-4">Status</th>
                        <th className="p-4">Created Date</th>
                        <th className="p-4 text-right pr-6">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {tenantUsers.map((u) => {
                        const isActive = u.is_active !== false && u.isActive !== false;
                        const isToggling = togglingUserId === u.id;
                        return (
                          <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                            <td className="p-4 pl-6">
                              <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs">
                                  {(u.email || "U").charAt(0).toUpperCase()}
                                </div>
                                <div>
                                  <p className="font-semibold text-slate-900 text-xs">{u.email}</p>
                                  {(u.first_name || u.last_name) && (
                                    <p className="text-[11px] text-slate-400">
                                      {[u.first_name, u.last_name].filter(Boolean).join(" ")}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </td>
                            <td className="p-4">
                              <Badge
                                variant="outline"
                                className={`text-xs font-semibold ${
                                  isActive
                                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                    : "bg-slate-100 text-slate-600 border-slate-200"
                                }`}
                              >
                                {isActive ? "Active" : "Deactivated"}
                              </Badge>
                            </td>
                            <td className="p-4 text-xs text-slate-500">
                              {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                            </td>
                            <td className="p-4 text-right pr-6">
                              <Button
                                variant="outline"
                                size="sm"
                                disabled={isToggling}
                                onClick={() => handleToggleUserActive(u)}
                                className={`rounded-xl text-xs font-semibold cursor-pointer ${
                                  isActive
                                    ? "border-amber-200 text-amber-700 hover:bg-amber-50 hover:text-amber-800"
                                    : "border-emerald-200 text-emerald-700 hover:bg-emerald-50 hover:text-emerald-800"
                                }`}
                              >
                                {isToggling ? (
                                  <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
                                ) : (
                                  <Power className="h-3.5 w-3.5 mr-1" />
                                )}
                                {isActive ? "Deactivate" : "Activate"}
                              </Button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
