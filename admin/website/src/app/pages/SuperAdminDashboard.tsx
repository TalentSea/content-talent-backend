import { useState, useEffect } from "react";
import { toast } from "sonner";
import { getTenants, createTenant, updateTenantStatus, ApiTenant } from "../services/apiService";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Loader2, Plus, RefreshCw, Users, Building, Clock, ChevronRight, LogIn } from "lucide-react";
import { Badge } from "../components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "../components/ui/dialog";

export default function SuperAdminDashboard() {
  const [activeTab, setActiveTab] = useState<"tenants" | "add" | "history">("tenants");
  const [tenants, setTenants] = useState<ApiTenant[]>([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState(false);

  const [newTenantName, setNewTenantName] = useState("");
  const [newAdminEmail, setNewAdminEmail] = useState("");
  const [newAdminPassword, setNewAdminPassword] = useState("");
  const [newAdminFirst, setNewAdminFirst] = useState("");
  const [newAdminLast, setNewAdminLast] = useState("");

  const [impersonateTenant, setImpersonateTenant] = useState<ApiTenant | null>(null);

  const loadTenants = async () => {
    setLoading(true);
    try {
      const data = await getTenants();
      setTenants(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTenants();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setAdding(true);
    try {
      await createTenant({
        name: newTenantName,
        adminEmail: newAdminEmail,
        adminPassword: newAdminPassword,
        adminFirstName: newAdminFirst,
        adminLastName: newAdminLast
      });
      toast.success(`Tenant "${newTenantName}" created successfully!`);
      setNewTenantName("");
      setNewAdminEmail("");
      setNewAdminPassword("");
      setNewAdminFirst("");
      setNewAdminLast("");
      setActiveTab("tenants");
      await loadTenants();
    } catch (err: any) {
      console.error(err);
      toast.error(err?.message || "Failed to create tenant.");
    } finally {
      setAdding(false);
    }
  };

  const handleToggle = async (tenant: ApiTenant) => {
    try {
      await updateTenantStatus(tenant.id, !tenant.isActive);
      await loadTenants();
      toast.success(`Tenant "${tenant.name}" ${tenant.isActive ? "deactivated" : "activated"} successfully.`);
    } catch (err: any) {
      console.error(err);
      toast.error(err?.message || "Failed to update tenant status.");
    }
  };

  const confirmImpersonate = () => {
    if (impersonateTenant) {
      toast.success(`Switching context to ${impersonateTenant.name}...`);
      localStorage.setItem("impersonating_tenant_id", impersonateTenant.id);
      localStorage.setItem("impersonating_tenant_name", impersonateTenant.name);
      window.location.reload();
    }
  };

  return (
    <div className="flex flex-col lg:flex-row h-full min-h-[calc(100vh-5rem)] bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
      {/* Sidebar */}
      <div className="w-full lg:w-64 border-r border-slate-200 bg-slate-50 flex flex-col">
        <div className="p-4 border-b border-slate-200">
          <h2 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Super Admin</h2>
        </div>
        <nav className="p-3 flex-1 space-y-1">
          <button
            onClick={() => setActiveTab("tenants")}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
              activeTab === "tenants" ? "bg-slate-900 text-white shadow-xs" : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900"
            }`}
          >
            <div className="flex items-center gap-3">
              <Building className="h-4 w-4" /> Tenants
            </div>
            {activeTab === "tenants" && <ChevronRight className="h-4 w-4 opacity-50" />}
          </button>
          
          <button
            onClick={() => setActiveTab("add")}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
              activeTab === "add" ? "bg-slate-900 text-white shadow-xs" : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900"
            }`}
          >
            <div className="flex items-center gap-3">
              <Plus className="h-4 w-4" /> Add Tenant
            </div>
            {activeTab === "add" && <ChevronRight className="h-4 w-4 opacity-50" />}
          </button>

          <button
            onClick={() => setActiveTab("history")}
            className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
              activeTab === "history" ? "bg-slate-900 text-white shadow-xs" : "text-slate-600 hover:bg-slate-200/50 hover:text-slate-900"
            }`}
          >
            <div className="flex items-center gap-3">
              <Clock className="h-4 w-4" /> History
            </div>
            {activeTab === "history" && <ChevronRight className="h-4 w-4 opacity-50" />}
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-6 lg:p-10 bg-white overflow-y-auto">
        {activeTab === "tenants" && (
          <div className="space-y-6 max-w-5xl">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-slate-900">Active Tenants</h1>
                <p className="text-slate-500 mt-1 text-sm">Select a tenant to access its dashboard or manage its status.</p>
              </div>
              <Button variant="outline" size="sm" onClick={loadTenants} disabled={loading} className="rounded-xl border-slate-200">
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Refresh
              </Button>
            </div>

            <div className="border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="p-4 font-semibold text-slate-700">Name</th>
                    <th className="p-4 font-semibold text-slate-700">Slug</th>
                    <th className="p-4 font-semibold text-slate-700">Status</th>
                    <th className="p-4 font-semibold text-slate-700 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {tenants.map(t => (
                    <tr 
                      key={t.id} 
                      className="hover:bg-slate-50 transition-colors cursor-pointer group"
                      onClick={() => setImpersonateTenant(t)}
                    >
                      <td className="p-4 font-medium text-slate-900 flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
                          {t.name.charAt(0).toUpperCase()}
                        </div>
                        {t.name}
                      </td>
                      <td className="p-4 text-slate-500 font-mono text-xs">{t.slug}</td>
                      <td className="p-4">
                        <Badge variant="outline" className={t.isActive ? "text-emerald-700 bg-emerald-50 border-emerald-200 shadow-none" : "text-slate-600 bg-slate-100 border-slate-200 shadow-none"}>
                          {t.isActive ? "Active" : "Deactivated"}
                        </Badge>
                      </td>
                      <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="sm" onClick={() => handleToggle(t)} className="text-slate-600 hover:text-slate-900 rounded-lg">
                          {t.isActive ? "Deactivate" : "Activate"}
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {tenants.length === 0 && !loading && (
                    <tr>
                      <td colSpan={4} className="p-8 text-center text-slate-500">
                        No tenants found. Click "Add Tenant" to provision one.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === "add" && (
          <div className="space-y-6 max-w-3xl">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">Provision New Tenant</h1>
              <p className="text-slate-500 mt-1 text-sm">Create a new studio instance.</p>
            </div>
            <Card className="bg-white border-slate-200 shadow-xs rounded-2xl">
              <CardContent className="pt-6">
                <form onSubmit={handleCreate} className="space-y-5">
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1.5">Tenant Name</Label>
                    <Input value={newTenantName} onChange={e => setNewTenantName(e.target.value)} required className="rounded-xl border-slate-200 focus:border-slate-900" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label className="text-xs font-semibold text-slate-700 block mb-1.5">Owner First Name</Label>
                      <Input value={newAdminFirst} onChange={e => setNewAdminFirst(e.target.value)} required className="rounded-xl border-slate-200 focus:border-slate-900" />
                    </div>
                    <div>
                      <Label className="text-xs font-semibold text-slate-700 block mb-1.5">Owner Last Name</Label>
                      <Input value={newAdminLast} onChange={e => setNewAdminLast(e.target.value)} required className="rounded-xl border-slate-200 focus:border-slate-900" />
                    </div>
                  </div>
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1.5">Owner Email</Label>
                    <Input type="email" value={newAdminEmail} onChange={e => setNewAdminEmail(e.target.value)} required className="rounded-xl border-slate-200 focus:border-slate-900" />
                  </div>
                  <div>
                    <Label className="text-xs font-semibold text-slate-700 block mb-1.5">Owner Password</Label>
                    <Input type="password" value={newAdminPassword} onChange={e => setNewAdminPassword(e.target.value)} required className="rounded-xl border-slate-200 focus:border-slate-900" />
                  </div>
                  <div className="pt-2">
                    <Button type="submit" disabled={adding} className="w-full h-11 bg-slate-900 text-white rounded-xl shadow-xs">
                      {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4 mr-2" />} Create Tenant
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === "history" && (
          <div className="space-y-6 max-w-5xl">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">Audit History</h1>
              <p className="text-slate-500 mt-1 text-sm">Recent super admin actions and system events.</p>
            </div>
            <div className="flex flex-col items-center justify-center p-12 text-slate-500 border border-slate-200 rounded-2xl border-dashed">
              <Clock className="h-8 w-8 mb-3 opacity-50" />
              <p>No recent history found.</p>
            </div>
          </div>
        )}
      </div>

      {/* Impersonation Dialog */}
      <Dialog open={!!impersonateTenant} onOpenChange={(open) => !open && setImpersonateTenant(null)}>
        <DialogContent className="sm:max-w-[425px] rounded-2xl">
          <DialogHeader>
            <DialogTitle>Access Tenant Dashboard</DialogTitle>
            <DialogDescription className="pt-2">
              Do you want to access <strong className="text-slate-900">{impersonateTenant?.name}</strong>?
              <br /><br />
              This will grant you full access to their dashboard, settings, and content as if you were the tenant owner.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="mt-4 gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setImpersonateTenant(null)} className="rounded-xl">Cancel</Button>
            <Button onClick={confirmImpersonate} className="bg-slate-900 text-white rounded-xl">
              <LogIn className="h-4 w-4 mr-2" /> Yes, Access Tenant
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
