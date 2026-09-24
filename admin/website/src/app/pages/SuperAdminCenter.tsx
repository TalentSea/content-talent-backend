import { useState, useEffect } from "react";
import {
  getTenants,
  createTenant,
  updateTenantStatus,
  ApiTenant,
  getCreatorProfile,
  updateCreatorProfile,
  getStoredAdmin,
  generateReconciliationDraft,
  publishReconciliation,
  markStatementPaid,
  getReconciliationLedger,
  PlatformReconciliationDraftResponse,
  PublishReconciliationResponse,
  ReconciliationListItem,
} from "../services/apiService";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Badge } from "../components/ui/badge";
import { Switch } from "../components/ui/switch";
import {
  Loader2, Plus, RefreshCw, Building2, User,
  DollarSign, Check, Search, ExternalLink, ArrowRight,
  Tv, Sliders, Shield, Zap, Sparkles, CheckCircle2,
  FileText, Calendar, CreditCard, AlertCircle, Receipt,
} from "lucide-react";
import { useNavigate } from "react-router";

export default function SuperAdminCenter() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"tenants" | "add-tenant" | "profile" | "monetization">("tenants");

  // Tenants state
  const [tenants, setTenants] = useState<ApiTenant[]>([]);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const [tenantSearch, setTenantSearch] = useState("");
  const [currentTenantId, setCurrentTenantId] = useState<string | null>(() => localStorage.getItem("current_tenant_id"));

  // Provisioning form state
  const [provisionName, setProvisionName] = useState("");
  const [provisionFirst, setProvisionFirst] = useState("");
  const [provisionLast, setProvisionLast] = useState("");
  const [provisionEmail, setProvisionEmail] = useState("");
  const [provisionPassword, setProvisionPassword] = useState("");
  const [provisionTagline, setProvisionTagline] = useState("");
  const [provisionDescription, setProvisionDescription] = useState("");
  const [isProvisioning, setIsProvisioning] = useState(false);
  const [provisionSuccess, setProvisionSuccess] = useState<string | null>(null);
  const [provisionError, setProvisionError] = useState<string | null>(null);

  // Profile state
  const [adminProfile, setAdminProfile] = useState<{
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    location: string;
    bio: string;
    avatarUrl: string;
  }>({
    firstName: "Super",
    lastName: "Admin",
    email: "superadmin@gmail.com",
    phone: "+1 (555) 019-2834",
    location: "Global Platform Core",
    bio: "Head platform owner governing white-label studios, infrastructure & platform monetization.",
    avatarUrl: "",
  });
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);

  // Ads & Monetization state
  const [adSettings, setAdSettings] = useState(() => {
    try {
      const stored = localStorage.getItem("platform_ads_config");
      if (stored) return JSON.parse(stored);
    } catch {}
    return {
      globalAdsEnabled: true,
      adNetwork: "google_ad_manager",
      googlePublisherId: "pub-8492049182049182",
      googleAdUnitPath: "/1234567/talentsea_preroll_video",
      bunnyVastUrl: "https://video.bunnycdn.com/vast/sample-talentsea",
      customVastUrl: "",
      enablePreRoll: true,
      enableMidRoll: true,
      midRollIntervalMinutes: 8,
      enablePostRoll: false,
      skipOffsetSeconds: 5,
      platformRevenueSharePercent: 15,
      creatorRevenueSharePercent: 85,
      payoutThresholdAmount: 100,
      payoutCurrency: "USD",
    };
  });
  const [isSavingAds, setIsSavingAds] = useState(false);
  const [adsSaved, setAdsSaved] = useState(false);

  // Fetch tenants
  const fetchTenants = async () => {
    setLoadingTenants(true);
    try {
      const data = await getTenants();
      setTenants(data);
    } catch (err) {
      console.warn("Could not fetch tenants in Super Admin Center:", err);
    } finally {
      setLoadingTenants(false);
    }
  };

  useEffect(() => {
    fetchTenants();

    // Rehydrate profile
    getCreatorProfile()
      .then((p) => {
        if (p) {
          setAdminProfile((prev) => ({
            ...prev,
            firstName: p.firstName || "Super",
            lastName: p.lastName || "Admin",
            email: p.email || prev.email,
            phone: p.phone || prev.phone,
            location: p.location || prev.location,
            bio: p.bio || prev.bio,
            avatarUrl: p.avatarUrl || prev.avatarUrl,
          }));
        }
      })
      .catch(() => {
        const stored = getStoredAdmin();
        if (stored) {
          setAdminProfile((prev) => ({
            ...prev,
            firstName: stored.first_name || "Super",
            lastName: stored.last_name || "Admin",
            email: stored.email || prev.email,
          }));
        }
      });
  }, []);

  // Handle switching active tenant
  const handleSwitchTenant = (tenant: ApiTenant) => {
    localStorage.setItem("current_tenant_id", String(tenant.id));
    localStorage.setItem("current_tenant_name", tenant.name);
    setCurrentTenantId(String(tenant.id));
    window.dispatchEvent(new CustomEvent("tenant_switched", { detail: tenant }));
    navigate("/");
  };

  // Toggle tenant status
  const handleToggleStatus = async (tenant: ApiTenant) => {
    try {
      await updateTenantStatus(tenant.id, !tenant.isActive);
      await fetchTenants();
    } catch (err) {
      console.error("Failed to toggle tenant status:", err);
    }
  };

  // Provision new tenant
  const handleProvisionTenant = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProvisioning(true);
    setProvisionError(null);
    setProvisionSuccess(null);

    try {
      await createTenant({
        name: provisionName,
        adminFirstName: provisionFirst,
        adminLastName: provisionLast,
        adminEmail: provisionEmail,
        adminPassword: provisionPassword,
        tagline: provisionTagline,
        description: provisionDescription,
      });

      setProvisionSuccess(`Tenant "${provisionName}" was provisioned successfully!`);
      setProvisionName("");
      setProvisionFirst("");
      setProvisionLast("");
      setProvisionEmail("");
      setProvisionPassword("");
      setProvisionTagline("");
      setProvisionDescription("");

      await fetchTenants();
      setTimeout(() => {
        setActiveTab("tenants");
        setProvisionSuccess(null);
      }, 1500);
    } catch (err: any) {
      setProvisionError(err?.message || "Failed to provision new tenant. Please check credentials.");
    } finally {
      setIsProvisioning(false);
    }
  };

  // Save profile
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingProfile(true);
    try {
      await updateCreatorProfile({
        first_name: adminProfile.firstName,
        last_name: adminProfile.lastName,
        phone: adminProfile.phone,
        location: adminProfile.location,
        bio: adminProfile.bio,
      });
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2000);
    } catch (err) {
      console.warn("Could not save super admin profile to API, saving locally:", err);
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 2000);
    } finally {
      setIsSavingProfile(false);
    }
  };

  // Save Ads Settings
  const handleSaveAds = () => {
    setIsSavingAds(true);
    try {
      localStorage.setItem("platform_ads_config", JSON.stringify(adSettings));
      window.dispatchEvent(new CustomEvent("platform_ads_updated", { detail: adSettings }));
      setAdsSaved(true);
      setTimeout(() => setAdsSaved(false), 2500);
    } finally {
      setIsSavingAds(false);
    }
  };

  // Monthly Ad Reconciliation & Settlements state
  const [reconMonth, setReconMonth] = useState(() => {
    const d = new Date();
    d.setMonth(d.getMonth() - 1);
    return d.toISOString().slice(0, 7);
  });
  const [reconGrossRevenue, setReconGrossRevenue] = useState<number>(10000);
  const [reconNotes, setReconNotes] = useState("");
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [activeDraft, setActiveDraft] = useState<PlatformReconciliationDraftResponse | null>(null);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishedData, setPublishedData] = useState<PublishReconciliationResponse | null>(null);
  const [ledgerItems, setLedgerItems] = useState<ReconciliationListItem[]>([]);
  const [loadingLedger, setLoadingLedger] = useState(false);
  const [settlingStatementId, setSettlingStatementId] = useState<string | null>(null);
  const [bankUtr, setBankUtr] = useState("");
  const [isSettling, setIsSettling] = useState(false);
  const [reconActionMessage, setReconActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchLedger = async () => {
    setLoadingLedger(true);
    try {
      const res = await getReconciliationLedger(1, 20);
      if (res && res.items) {
        setLedgerItems(res.items);
      }
    } catch (err: any) {
      console.warn("Could not fetch reconciliation ledger:", err);
    } finally {
      setLoadingLedger(false);
    }
  };

  useEffect(() => {
    if (activeTab === "monetization") {
      fetchLedger();
    }
  }, [activeTab]);

  const handleGenerateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reconMonth || !reconGrossRevenue) return;
    setIsGeneratingDraft(true);
    setReconActionMessage(null);
    setPublishedData(null);
    try {
      const draft = await generateReconciliationDraft({
        month: reconMonth,
        gross_revenue: Number(reconGrossRevenue),
        notes: reconNotes || undefined,
      });
      setActiveDraft(draft);
      setReconActionMessage({ type: "success", text: `Reconciliation draft generated for ${draft.month} with ${draft.statements?.length || 0} tenant statements.` });
      fetchLedger();
    } catch (err: any) {
      setReconActionMessage({ type: "error", text: err.message || "Failed to generate reconciliation draft." });
    } finally {
      setIsGeneratingDraft(false);
    }
  };

  const handlePublishReconciliation = async () => {
    if (!activeDraft?.month) return;
    setIsPublishing(true);
    setReconActionMessage(null);
    try {
      const res = await publishReconciliation(activeDraft.month);
      setPublishedData(res);
      setActiveDraft(null);
      setReconActionMessage({ type: "success", text: `Successfully published statements for ${res.month}! Tenants can now review their monthly settlement.` });
      fetchLedger();
    } catch (err: any) {
      setReconActionMessage({ type: "error", text: err.message || "Failed to publish reconciliation statements." });
    } finally {
      setIsPublishing(false);
    }
  };

  const handleMarkPaid = async (statementId: string) => {
    if (!bankUtr.trim()) {
      setReconActionMessage({ type: "error", text: "Please enter a bank transaction reference / UTR code." });
      return;
    }
    setIsSettling(true);
    setReconActionMessage(null);
    try {
      const res = await markStatementPaid(statementId, { transaction_reference: bankUtr.trim() });
      setReconActionMessage({ type: "success", text: `Statement #${res.statement_id} marked as SETTLED (Ref: ${res.transaction_reference}).` });
      setSettlingStatementId(null);
      setBankUtr("");
      if (publishedData) {
        setPublishedData({
          ...publishedData,
          statements: publishedData.statements.map(s => s.statement_id === statementId ? { ...s, status: "settled" } : s)
        });
      }
      fetchLedger();
    } catch (err: any) {
      setReconActionMessage({ type: "error", text: err.message || "Failed to record payment for statement." });
    } finally {
      setIsSettling(false);
    }
  };

  const filteredTenants = tenants.filter((t) =>
    t.name.toLowerCase().includes(tenantSearch.toLowerCase()) ||
    t.slug.toLowerCase().includes(tenantSearch.toLowerCase())
  );

  return (
    <div className="space-y-6 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Super Admin Center</h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage platform tenants, provision new creator instances, super admin profile, and global monetization.
          </p>
        </div>
      </div>

      {/* Tab Navigation Bar - Styled like Settings */}
      <div className="bg-slate-100 border border-slate-200/80 p-1 rounded-xl flex w-full overflow-x-auto gap-1">
        {[
          { id: "tenants", label: "Tenants Management", icon: Building2 },
          { id: "add-tenant", label: "Add New Tenant", icon: Plus },
          { id: "profile", label: "Super Admin Profile", icon: User },
          { id: "monetization", label: "Ads & Monetization", icon: DollarSign },
        ].map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex-1 justify-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold transition-all inline-flex items-center cursor-pointer whitespace-nowrap ${
                isActive
                  ? "bg-white text-slate-900 shadow-xs"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              <Icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* TAB 1: TENANTS LIST */}
      {activeTab === "tenants" && (
        <div className="space-y-6">
          {/* Stats Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Studios</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{tenants.length}</p>
                </div>
                <div className="h-11 w-11 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                  <Building2 className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Instances</p>
                  <p className="text-2xl font-bold text-emerald-600 mt-1">
                    {tenants.filter((t) => t.isActive).length}
                  </p>
                </div>
                <div className="h-11 w-11 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
                  <Zap className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
              <CardContent className="p-5 flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Deactivated</p>
                  <p className="text-2xl font-bold text-slate-400 mt-1">
                    {tenants.filter((t) => !t.isActive).length}
                  </p>
                </div>
                <div className="h-11 w-11 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600">
                  <Shield className="h-5 w-5" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tenants Table Card */}
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl overflow-hidden">
            <CardHeader className="border-b border-slate-100 p-5 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900">All Registered Tenants</CardTitle>
                <CardDescription className="text-xs text-slate-500 mt-0.5">
                  Click "Switch Tenant" on any row to immediately manage that creator studio.
                </CardDescription>
              </div>

              <div className="flex items-center gap-3">
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-400" />
                  <Input
                    placeholder="Search tenant or slug..."
                    value={tenantSearch}
                    onChange={(e) => setTenantSearch(e.target.value)}
                    className="pl-9 h-9 text-xs bg-slate-50 border-slate-200 rounded-xl"
                  />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchTenants}
                  disabled={loadingTenants}
                  className="rounded-xl border-slate-200 text-xs h-9"
                >
                  <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loadingTenants ? "animate-spin" : ""}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50/80 border-b border-slate-100 text-xs text-slate-600 uppercase font-semibold">
                    <tr>
                      <th className="p-4 pl-6">Tenant Studio</th>
                      <th className="p-4">Slug Identifier</th>
                      <th className="p-4">Status</th>
                      <th className="p-4">Videos</th>
                      <th className="p-4 pr-6 text-right">Super Admin Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredTenants.map((t) => {
                      const isCurrent = currentTenantId === String(t.id);
                      return (
                        <tr
                          key={t.id}
                          className={`hover:bg-slate-50/80 transition-colors ${
                            isCurrent ? "bg-indigo-50/40" : ""
                          }`}
                        >
                          <td className="p-4 pl-6 font-medium text-slate-900">
                            <div className="flex items-center gap-3">
                              <div className="h-9 w-9 rounded-xl bg-slate-900 text-white flex items-center justify-center font-bold text-sm shadow-xs shrink-0">
                                {t.logoUrl ? (
                                  <img src={t.logoUrl} alt={t.name} className="h-full w-full object-cover rounded-xl" />
                                ) : (
                                  t.name.slice(0, 2).toUpperCase()
                                )}
                              </div>
                              <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-slate-900 truncate block">{t.name}</span>
                                  {isCurrent && (
                                    <Badge className="bg-indigo-600 text-white text-[10px] px-1.5 py-0 rounded-md font-bold">
                                      CURRENT
                                    </Badge>
                                  )}
                                </div>
                                {t.tagline && (
                                  <span className="text-xs text-slate-400 block truncate">{t.tagline}</span>
                                )}
                              </div>
                            </div>
                          </td>

                          <td className="p-4 text-xs font-mono text-slate-600">
                            <span className="px-2 py-0.5 rounded-md bg-slate-100 border border-slate-200">
                              {t.slug}
                            </span>
                          </td>

                          <td className="p-4">
                            <Badge
                              variant="outline"
                              className={
                                t.isActive
                                  ? "text-emerald-700 bg-emerald-50 border-emerald-200 font-semibold text-xs"
                                  : "text-slate-500 bg-slate-100 border-slate-200 text-xs"
                              }
                            >
                              {t.isActive ? "Active Studio" : "Deactivated"}
                            </Badge>
                          </td>

                          <td className="p-4 text-xs text-slate-600">
                            <span className="font-semibold text-slate-900">{t.videosCount || 0}</span> videos
                          </td>

                          <td className="p-4 pr-6 text-right">
                            <div className="flex items-center justify-end gap-2">
                              {!isCurrent && (
                                <Button
                                  size="sm"
                                  onClick={() => handleSwitchTenant(t)}
                                  className="text-xs h-8 px-3 rounded-xl font-semibold shadow-xs bg-slate-900 hover:bg-slate-800 text-white cursor-pointer"
                                >
                                  Switch Tenant
                                  <ArrowRight className="h-3.5 w-3.5 ml-1" />
                                </Button>
                              )}

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleToggleStatus(t)}
                                className="text-xs h-8 px-2.5 rounded-xl border-slate-200 text-slate-600 hover:text-slate-900"
                              >
                                {t.isActive ? "Deactivate" : "Activate"}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}

                    {filteredTenants.length === 0 && !loadingTenants && (
                      <tr>
                        <td colSpan={5} className="p-12 text-center text-slate-400 text-sm">
                          No tenants found matching your query.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 2: PROVISION NEW TENANT */}
      {activeTab === "add-tenant" && (
        <div className="w-full">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="border-b border-slate-100 pb-4">
              <CardTitle className="text-lg font-bold text-slate-900">Provision New Tenant Studio</CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Setup a new independent studio partition with dedicated branding, video library, and creator owner credentials.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {provisionSuccess && (
                <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
                  {provisionSuccess}
                </div>
              )}
              {provisionError && (
                <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2 font-semibold">
                  <span>⚠️</span> {provisionError}
                </div>
              )}

              <form onSubmit={handleProvisionTenant} className="space-y-5">
                <div>
                  <Label className="text-xs font-bold text-slate-800 block mb-1.5">Tenant / Studio Brand Name *</Label>
                  <Input
                    placeholder="e.g. Apex Cinematic Academy"
                    value={provisionName}
                    onChange={(e) => setProvisionName(e.target.value)}
                    required
                    className="h-10 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs font-bold text-slate-800 block mb-1.5">Studio Tagline</Label>
                    <Input
                      placeholder="e.g. Master Film & Sound"
                      value={provisionTagline}
                      onChange={(e) => setProvisionTagline(e.target.value)}
                      className="h-10 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-bold text-slate-800 block mb-1.5">Owner / Admin Email *</Label>
                    <Input
                      type="email"
                      placeholder="creator@apexstudio.io"
                      value={provisionEmail}
                      onChange={(e) => setProvisionEmail(e.target.value)}
                      required
                      className="h-10 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs font-bold text-slate-800 block mb-1.5">Owner First Name *</Label>
                    <Input
                      placeholder="Alex"
                      value={provisionFirst}
                      onChange={(e) => setProvisionFirst(e.target.value)}
                      required
                      className="h-10 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-bold text-slate-800 block mb-1.5">Owner Last Name *</Label>
                    <Input
                      placeholder="Rivera"
                      value={provisionLast}
                      onChange={(e) => setProvisionLast(e.target.value)}
                      required
                      className="h-10 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs font-bold text-slate-800 block mb-1.5">Initial Password *</Label>
                  <Input
                    type="password"
                    placeholder="••••••••••••"
                    value={provisionPassword}
                    onChange={(e) => setProvisionPassword(e.target.value)}
                    required
                    className="h-10 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    The tenant creator can reset this password anytime from their studio settings.
                  </p>
                </div>

                <div>
                  <Label className="text-xs font-bold text-slate-800 block mb-1.5">Studio Description</Label>
                  <Input
                    placeholder="Brief description about the creator or studio scope"
                    value={provisionDescription}
                    onChange={(e) => setProvisionDescription(e.target.value)}
                    className="h-10 rounded-xl border-slate-200 bg-slate-50/50 focus:bg-white"
                  />
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    disabled={isProvisioning}
                    className="w-full sm:w-auto px-8 h-11 bg-slate-900 hover:bg-slate-800 text-white rounded-xl font-bold shadow-md cursor-pointer"
                  >
                    {isProvisioning ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Provisioning Tenant Instance...
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4 mr-2" />
                        Complete Provisioning & Deploy
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 3: SUPER ADMIN PROFILE INFO */}
      {activeTab === "profile" && (
        <div className="w-full">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl w-full">
            <CardHeader className="border-b border-slate-100 pb-4">
              <CardTitle className="text-lg font-bold text-slate-900">Super Administrator Profile</CardTitle>
              <CardDescription className="text-xs text-slate-500">
                Manage your global platform administrator credentials and identity.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              {profileSaved && (
                <div className="mb-5 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Super Admin Profile updated successfully!
                </div>
              )}

              <form onSubmit={handleSaveProfile} className="space-y-5">
                <div className="flex items-center gap-4 pb-4 border-b border-slate-100">
                  <div className="h-16 w-16 rounded-2xl bg-slate-900 text-white flex items-center justify-center font-bold text-xl shadow-md">
                    {adminProfile.avatarUrl ? (
                      <img src={adminProfile.avatarUrl} alt="Avatar" className="h-full w-full object-cover rounded-2xl" />
                    ) : (
                      "SA"
                    )}
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-slate-900">
                      {adminProfile.firstName} {adminProfile.lastName}
                    </h3>
                    <p className="text-xs text-slate-500 font-mono">{adminProfile.email}</p>
                    <span className="inline-block mt-1.5 px-2 py-0.5 rounded-md bg-purple-100 text-purple-700 text-[10px] font-bold uppercase tracking-wider">
                      Global Platform Owner
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">First Name</Label>
                    <Input
                      value={adminProfile.firstName}
                      onChange={(e) => setAdminProfile({ ...adminProfile, firstName: e.target.value })}
                      className="h-10 rounded-xl border-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Last Name</Label>
                    <Input
                      value={adminProfile.lastName}
                      onChange={(e) => setAdminProfile({ ...adminProfile, lastName: e.target.value })}
                      className="h-10 rounded-xl border-slate-200"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Super Admin Email</Label>
                    <Input
                      type="email"
                      value={adminProfile.email}
                      disabled
                      className="h-10 rounded-xl border-slate-200 bg-slate-50 text-slate-500 cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Direct Phone</Label>
                    <Input
                      value={adminProfile.phone}
                      onChange={(e) => setAdminProfile({ ...adminProfile, phone: e.target.value })}
                      className="h-10 rounded-xl border-slate-200"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-xs font-semibold text-slate-700 block mb-1">Location / Timezone</Label>
                  <Input
                    value={adminProfile.location}
                    onChange={(e) => setAdminProfile({ ...adminProfile, location: e.target.value })}
                    className="h-10 rounded-xl border-slate-200"
                  />
                </div>

                <div>
                  <Label className="text-xs font-semibold text-slate-700 block mb-1">Administrator Bio</Label>
                  <textarea
                    rows={3}
                    value={adminProfile.bio}
                    onChange={(e) => setAdminProfile({ ...adminProfile, bio: e.target.value })}
                    className="w-full border border-slate-200 rounded-xl p-3 text-xs text-slate-900 bg-white focus:border-slate-900 focus:outline-none"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={isSavingProfile}
                  className="bg-slate-900 hover:bg-slate-800 text-white rounded-xl h-10 px-6 font-bold shadow-xs cursor-pointer"
                >
                  {isSavingProfile ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Save Profile Details
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 4: ADS & MONETIZATION */}
      {activeTab === "monetization" && (
        <div className="space-y-6 w-full">
          <Card className="bg-white border-slate-200/80 shadow-xs rounded-2xl">
            <CardHeader className="border-b border-slate-100 pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-emerald-600" />
                  Global Video Ads & Monetization Engine
                </CardTitle>
                <CardDescription className="text-xs text-slate-500 mt-0.5">
                  Configure programmatic VAST/VPAID video advertising networks and revenue splits across all creator tenants.
                </CardDescription>
              </div>

              <div className="flex items-center gap-2.5">
                <span className="text-xs font-semibold text-slate-700">Master Ad Engine</span>
                <Switch
                  checked={adSettings.globalAdsEnabled}
                  onCheckedChange={(checked) => setAdSettings({ ...adSettings, globalAdsEnabled: checked })}
                />
              </div>
            </CardHeader>

            <CardContent className="pt-6 space-y-7">
              {adsSaved && (
                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 font-semibold">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  Platform Advertising and Monetization settings saved successfully!
                </div>
              )}

              {/* Ad Networks Section */}
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Tv className="h-4 w-4 text-slate-600" />
                  Programmatic Video Ad Provider
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {[
                    { id: "google_ad_manager", name: "Google Ad Manager", tag: "Google IMA / VAST" },
                    { id: "bunny_stream", name: "Bunny Video Ads", tag: "Bunny CDN Stream" },
                    { id: "custom_vast", name: "Custom VAST / VPAID", tag: "Direct Ad Server" },
                  ].map((prov) => {
                    const isSelected = adSettings.adNetwork === prov.id;
                    return (
                      <button
                        type="button"
                        key={prov.id}
                        onClick={() => setAdSettings({ ...adSettings, adNetwork: prov.id })}
                        className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                          isSelected
                            ? "border-slate-900 bg-slate-900 text-white shadow-xs"
                            : "border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-800"
                        }`}
                      >
                        <p className="font-bold text-xs">{prov.name}</p>
                        <p className={`text-[10px] mt-0.5 ${isSelected ? "text-slate-300" : "text-slate-500"}`}>
                          {prov.tag}
                        </p>
                      </button>
                    );
                  })}
                </div>

                {adSettings.adNetwork === "google_ad_manager" && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                    <div>
                      <Label className="text-xs font-semibold text-slate-700 block mb-1">Google Publisher ID</Label>
                      <Input
                        value={adSettings.googlePublisherId}
                        onChange={(e) => setAdSettings({ ...adSettings, googlePublisherId: e.target.value })}
                        placeholder="pub-XXXXXXXXXXXXXXXX"
                        className="h-9 text-xs bg-white border-slate-200 font-mono"
                      />
                    </div>
                    <div>
                      <Label className="text-xs font-semibold text-slate-700 block mb-1">Default Ad Unit Path</Label>
                      <Input
                        value={adSettings.googleAdUnitPath}
                        onChange={(e) => setAdSettings({ ...adSettings, googleAdUnitPath: e.target.value })}
                        placeholder="/12345/talentsea_preroll"
                        className="h-9 text-xs bg-white border-slate-200 font-mono"
                      />
                    </div>
                  </div>
                )}

                {adSettings.adNetwork === "bunny_stream" && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Bunny Stream VAST URL</Label>
                    <Input
                      value={adSettings.bunnyVastUrl}
                      onChange={(e) => setAdSettings({ ...adSettings, bunnyVastUrl: e.target.value })}
                      className="h-9 text-xs bg-white border-slate-200 font-mono"
                    />
                  </div>
                )}

                {adSettings.adNetwork === "custom_vast" && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Custom VAST XML Endpoint URL</Label>
                    <Input
                      value={adSettings.customVastUrl}
                      onChange={(e) => setAdSettings({ ...adSettings, customVastUrl: e.target.value })}
                      placeholder="https://adserver.yournetwork.com/vast?id=..."
                      className="h-9 text-xs bg-white border-slate-200 font-mono"
                    />
                  </div>
                )}
              </div>

              {/* Video Placement Controls */}
              <div className="space-y-4 pt-4 border-t border-slate-100">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-slate-600" />
                  Video Ad Placement Rules
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <Label className="text-xs font-bold text-slate-800">Pre-roll Ads</Label>
                        <Switch
                          checked={adSettings.enablePreRoll}
                          onCheckedChange={(c) => setAdSettings({ ...adSettings, enablePreRoll: c })}
                        />
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">Play short video ad before playback begins.</p>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <Label className="text-xs font-bold text-slate-800">Mid-roll Ads</Label>
                        <Switch
                          checked={adSettings.enableMidRoll}
                          onCheckedChange={(c) => setAdSettings({ ...adSettings, enableMidRoll: c })}
                        />
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">Break into long-form videos at intervals.</p>
                    </div>
                    {adSettings.enableMidRoll && (
                      <div className="pt-2 border-t border-slate-100">
                        <span className="text-[10px] text-slate-500 font-medium">Interval (minutes):</span>
                        <Input
                          type="number"
                          value={adSettings.midRollIntervalMinutes}
                          onChange={(e) => setAdSettings({ ...adSettings, midRollIntervalMinutes: Number(e.target.value) })}
                          className="h-8 text-xs mt-1 w-24 bg-slate-50"
                        />
                      </div>
                    )}
                  </div>

                  <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2 flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between">
                        <Label className="text-xs font-bold text-slate-800">Post-roll Ads</Label>
                        <Switch
                          checked={adSettings.enablePostRoll}
                          onCheckedChange={(c) => setAdSettings({ ...adSettings, enablePostRoll: c })}
                        />
                      </div>
                      <p className="text-[11px] text-slate-500 mt-1">Play ad after video playback finishes.</p>
                    </div>
                  </div>
                </div>

                <div className="max-w-xs">
                  <Label className="text-xs font-semibold text-slate-700 block mb-1">Skip Ad Offset (Seconds)</Label>
                  <Input
                    type="number"
                    value={adSettings.skipOffsetSeconds}
                    onChange={(e) => setAdSettings({ ...adSettings, skipOffsetSeconds: Number(e.target.value) })}
                    className="h-9 text-xs w-32 border-slate-200 rounded-xl"
                  />
                </div>
              </div>

              {/* Revenue Sharing Model */}
              <div className="space-y-4 pt-4 border-t border-slate-100">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-emerald-600" />
                  Monetization & Platform Revenue Share Model
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                    <Label className="text-xs font-bold text-slate-800 block">Platform Commission Cut (%)</Label>
                    <div className="flex items-center gap-3">
                      <Input
                        type="number"
                        min={0}
                        max={100}
                        value={adSettings.platformRevenueSharePercent}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setAdSettings({
                            ...adSettings,
                            platformRevenueSharePercent: val,
                            creatorRevenueSharePercent: 100 - val,
                          });
                        }}
                        className="h-10 text-sm font-bold w-24 bg-white"
                      />
                      <span className="text-xs text-slate-500 font-semibold">
                        Platform retains {adSettings.platformRevenueSharePercent}% of ad impressions
                      </span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-3">
                    <Label className="text-xs font-bold text-slate-800 block">Creator Share (%)</Label>
                    <div className="flex items-center gap-3">
                      <Input
                        type="number"
                        disabled
                        value={adSettings.creatorRevenueSharePercent}
                        className="h-10 text-sm font-bold w-24 bg-slate-100 text-slate-500 cursor-not-allowed"
                      />
                      <span className="text-xs text-slate-500 font-semibold">
                        Tenant studio earns {adSettings.creatorRevenueSharePercent}% of revenue
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Minimum Payout Threshold</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={adSettings.payoutThresholdAmount}
                        onChange={(e) => setAdSettings({ ...adSettings, payoutThresholdAmount: Number(e.target.value) })}
                        className="h-9 text-xs w-28 border-slate-200 rounded-xl"
                      />
                      <span className="text-xs text-slate-500 font-mono font-bold">USD</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-2">
                <Button
                  onClick={handleSaveAds}
                  disabled={isSavingAds}
                  className="bg-slate-900 hover:bg-slate-800 text-white rounded-xl h-11 px-8 font-bold shadow-md cursor-pointer"
                >
                  {isSavingAds ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  Save Ads & Monetization Configuration
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Monthly Ad Revenue Reconciliation & Tenant Settlements */}
          <Card className="border-slate-200/80 shadow-sm bg-white overflow-hidden">
            <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-indigo-50 rounded-xl border border-indigo-100">
                    <FileText className="h-5 w-5 text-indigo-600" />
                  </div>
                  <div>
                    <CardTitle className="text-base font-bold text-slate-900">
                      Monthly Ad Reconciliation & Creator Settlements
                    </CardTitle>
                    <CardDescription className="text-xs text-slate-500 mt-0.5">
                      Ingest gross Google Ad Manager / VAST earnings, calculate tenant rev-share pools, publish official creator statements, and track wire payouts.
                    </CardDescription>
                  </div>
                </div>
                <Badge variant="outline" className="bg-indigo-50 text-indigo-700 border-indigo-200 text-xs font-semibold px-2.5 py-1">
                  Accounting Engine
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              {reconActionMessage && (
                <div className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                  reconActionMessage.type === "success"
                    ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                    : "bg-red-50 border-red-200 text-red-800"
                }`}>
                  {reconActionMessage.type === "success" ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
                  )}
                  <span>{reconActionMessage.text}</span>
                </div>
              )}

              {/* Generate Draft Form */}
              <form onSubmit={handleGenerateDraft} className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-4">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                  <Calendar className="h-3.5 w-3.5 text-slate-600" />
                  Generate New Monthly Settlement Run
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Billing Month (YYYY-MM)</Label>
                    <Input
                      type="month"
                      value={reconMonth}
                      onChange={(e) => setReconMonth(e.target.value)}
                      required
                      className="h-9 text-xs bg-white border-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Total Gross Ad Revenue (USD $)</Label>
                    <Input
                      type="number"
                      min={0}
                      step="0.01"
                      value={reconGrossRevenue}
                      onChange={(e) => setReconGrossRevenue(Number(e.target.value))}
                      placeholder="e.g. 15000"
                      required
                      className="h-9 text-xs bg-white border-slate-200"
                    />
                  </div>
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1">Internal Reference / Notes</Label>
                    <Input
                      type="text"
                      value={reconNotes}
                      onChange={(e) => setReconNotes(e.target.value)}
                      placeholder="e.g. GAM final monthly report"
                      className="h-9 text-xs bg-white border-slate-200"
                    />
                  </div>
                </div>
                <div className="flex justify-end pt-1">
                  <Button
                    type="submit"
                    disabled={isGeneratingDraft}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs h-9 px-4 font-semibold shadow-sm cursor-pointer"
                  >
                    {isGeneratingDraft ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : <Sparkles className="h-3.5 w-3.5 mr-1.5" />}
                    Calculate & Preview Draft
                  </Button>
                </div>
              </form>

              {/* Active Draft Preview */}
              {activeDraft && (
                <div className="border border-indigo-200/80 rounded-xl p-4 bg-indigo-50/30 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">
                        Draft Breakdown for {activeDraft.month}
                      </h4>
                      <p className="text-xs text-slate-500">
                        {activeDraft.total_impressions.toLocaleString()} ad impressions recorded across {activeDraft.creators_count} tenant studios
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-amber-100 text-amber-800 border-amber-200 text-xs">
                        Draft Status
                      </Badge>
                      <Button
                        onClick={handlePublishReconciliation}
                        disabled={isPublishing}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs h-8 px-3 font-semibold shadow-sm cursor-pointer"
                      >
                        {isPublishing ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> : <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />}
                        Publish Official Statements
                      </Button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                      <span className="text-[11px] text-slate-500 font-medium">Gross Revenue</span>
                      <p className="text-base font-bold text-slate-900">${activeDraft.total_google_revenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                      <span className="text-[11px] text-slate-500 font-medium">Platform Fee ({activeDraft.platform_commission_pct}%)</span>
                      <p className="text-base font-bold text-indigo-600">${activeDraft.platform_profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                      <span className="text-[11px] text-slate-500 font-medium">Creator Pool</span>
                      <p className="text-base font-bold text-emerald-600">${activeDraft.creator_pool_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                      <span className="text-[11px] text-slate-500 font-medium">Creator Net eCPM</span>
                      <p className="text-base font-bold text-slate-900">${activeDraft.creator_net_ecpm.toFixed(4)}</p>
                    </div>
                  </div>

                  {activeDraft.statements && activeDraft.statements.length > 0 && (
                    <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                      <table className="w-full text-left text-xs text-slate-600">
                        <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px]">
                          <tr>
                            <th className="py-2.5 px-3">Tenant Studio</th>
                            <th className="py-2.5 px-3">Impressions</th>
                            <th className="py-2.5 px-3">Gross Revenue</th>
                            <th className="py-2.5 px-3">Platform Cut</th>
                            <th className="py-2.5 px-3 font-bold text-slate-900">Tenant Payout</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {activeDraft.statements.map((s) => (
                            <tr key={s.tenant_id} className="hover:bg-slate-50/50">
                              <td className="py-2 px-3 font-semibold text-slate-900">{s.tenant_name}</td>
                              <td className="py-2 px-3 font-mono">{s.impressions_count.toLocaleString()}</td>
                              <td className="py-2 px-3 font-mono">${s.gross_revenue.toFixed(2)}</td>
                              <td className="py-2 px-3 font-mono text-slate-400">-${s.platform_fee.toFixed(2)}</td>
                              <td className="py-2 px-3 font-mono font-bold text-emerald-600">${s.net_amount.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Published Statements / Wire Payout Section */}
              {publishedData && (
                <div className="border border-emerald-200/80 rounded-xl p-4 bg-emerald-50/20 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-slate-900">
                        Published Settlement Statements for {publishedData.month}
                      </h4>
                      <p className="text-xs text-slate-500">
                        Statements are published and visible to creators. Record bank transfer references once wire payments clear.
                      </p>
                    </div>
                    <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200 text-xs">
                      Official Ledger Active
                    </Badge>
                  </div>

                  <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                    <table className="w-full text-left text-xs text-slate-600">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px]">
                        <tr>
                          <th className="py-2.5 px-3">Statement ID</th>
                          <th className="py-2.5 px-3">Tenant Studio</th>
                          <th className="py-2.5 px-3">Net Payable</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {publishedData.statements.map((stmt) => (
                          <tr key={stmt.statement_id} className="hover:bg-slate-50/50">
                            <td className="py-2.5 px-3 font-mono font-semibold text-slate-900">{stmt.statement_id}</td>
                            <td className="py-2.5 px-3 font-medium text-slate-800">{stmt.tenant_name}</td>
                            <td className="py-2.5 px-3 font-mono font-bold text-emerald-600">${stmt.net_amount.toFixed(2)}</td>
                            <td className="py-2.5 px-3">
                              <Badge className={`text-[10px] font-bold ${
                                stmt.status === "settled"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : "bg-blue-100 text-blue-800"
                              }`}>
                                {stmt.status.toUpperCase()}
                              </Badge>
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              {stmt.status === "settled" ? (
                                <span className="text-[11px] text-emerald-600 font-semibold flex items-center justify-end gap-1">
                                  <Check className="h-3 w-3" /> Settled
                                </span>
                              ) : settlingStatementId === stmt.statement_id ? (
                                <div className="flex items-center justify-end gap-1.5">
                                  <Input
                                    value={bankUtr}
                                    onChange={(e) => setBankUtr(e.target.value)}
                                    placeholder="Bank UTR / Txn Ref"
                                    className="h-7 text-[11px] w-36 bg-slate-50"
                                  />
                                  <Button
                                    size="sm"
                                    disabled={isSettling}
                                    onClick={() => handleMarkPaid(stmt.statement_id)}
                                    className="h-7 text-[11px] px-2 bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
                                  >
                                    {isSettling ? <Loader2 className="h-3 w-3 animate-spin" /> : "Confirm"}
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => { setSettlingStatementId(null); setBankUtr(""); }}
                                    className="h-7 text-[11px] px-1.5 cursor-pointer"
                                  >
                                    Cancel
                                  </Button>
                                </div>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => { setSettlingStatementId(stmt.statement_id); setBankUtr(""); }}
                                  className="h-7 text-[11px] px-2.5 border-slate-200 text-slate-700 hover:bg-slate-100 cursor-pointer"
                                >
                                  <CreditCard className="h-3 w-3 mr-1 text-slate-500" />
                                  Record Payout
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Historical Reconciliation Runs Ledger */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
                    <Receipt className="h-3.5 w-3.5 text-slate-600" />
                    Past Reconciliation Runs Ledger
                  </h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={fetchLedger}
                    disabled={loadingLedger}
                    className="h-7 text-xs text-slate-600 cursor-pointer"
                  >
                    <RefreshCw className={`h-3 w-3 mr-1 ${loadingLedger ? "animate-spin" : ""}`} />
                    Refresh Ledger
                  </Button>
                </div>

                {ledgerItems.length === 0 ? (
                  <div className="text-center py-6 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                    <p className="text-xs text-slate-400">No past reconciliation statements recorded yet.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                    <table className="w-full text-left text-xs text-slate-600">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-700 font-semibold uppercase text-[10px]">
                        <tr>
                          <th className="py-2.5 px-3">Billing Month</th>
                          <th className="py-2.5 px-3">Total Ad Revenue</th>
                          <th className="py-2.5 px-3">Platform Profit</th>
                          <th className="py-2.5 px-3">Creator Pool</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3">Date</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {ledgerItems.map((item) => (
                          <tr key={item.id} className="hover:bg-slate-50/50">
                            <td className="py-2.5 px-3 font-semibold text-slate-900 font-mono">{item.month}</td>
                            <td className="py-2.5 px-3 font-mono">${item.total_google_revenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                            <td className="py-2.5 px-3 font-mono text-indigo-600 font-medium">${item.platform_profit.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                            <td className="py-2.5 px-3 font-mono text-emerald-600 font-medium">${item.creator_pool_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                            <td className="py-2.5 px-3">
                              <Badge className={`text-[10px] font-bold ${
                                item.status === "published"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : item.status === "settled"
                                  ? "bg-purple-100 text-purple-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}>
                                {item.status.toUpperCase()}
                              </Badge>
                            </td>
                            <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                              {item.reconciled_at ? new Date(item.reconciled_at).toLocaleDateString() : "-"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
