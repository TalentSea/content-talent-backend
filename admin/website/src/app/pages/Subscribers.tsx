import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Label } from "../components/ui/label";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../components/ui/table";
import {
  Search,
  MoreVertical,
  Mail,
  UserX,
  Crown,
  Users,
  TrendingUp,
  DollarSign,
  SlidersHorizontal,
  X,
  Calendar,
  Loader2,
  RefreshCw,
} from "lucide-react";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import {
  getSubscribers,
  getDashboardStats,
  getDashboardSubscriptionBreakdown,
  getSubscriptionPlans,
  ApiSubscriber,
  ApiDashboardStats,
  ApiSubscriptionBreakdown,
  ApiSubscriptionPlan,
} from "../services/apiService";

function DatePickerDialog({ open, onClose, value, onChange }: {
  open: boolean; onClose: () => void; value: string; onChange: (v: string) => void;
}) {
  const [local, setLocal] = useState(value);
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-xs bg-white border border-slate-200 text-slate-900 shadow-2xl rounded-2xl">
        <DialogHeader>
          <DialogTitle className="text-base font-bold text-slate-900">Filter by Date</DialogTitle>
          <DialogDescription className="text-xs text-slate-500">Show subscribers who joined on this date</DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <Input type="date" value={local} onChange={(e) => setLocal(e.target.value)} className="bg-white border-slate-200 text-slate-900 rounded-xl text-xs h-10" />
        </div>
        <DialogFooter className="gap-2 pt-2 border-t border-slate-100">
          <Button variant="outline" className="border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl" onClick={() => { onChange(""); setLocal(""); onClose(); }}>Clear</Button>
          <Button className="bg-slate-900 hover:bg-slate-800 text-white rounded-xl shadow-xs" onClick={() => { onChange(local); onClose(); }}>Apply</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Subscribers() {
  const [subscribers, setSubscribers] = useState<ApiSubscriber[]>([]);
  const [stats, setStats] = useState<ApiDashboardStats | null>(null);
  const [breakdown, setBreakdown] = useState<ApiSubscriptionBreakdown | null>(null);
  const [availablePlans, setAvailablePlans] = useState<ApiSubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filterPlan, setFilterPlan] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterDate, setFilterDate] = useState("");
  const [datePickerOpen, setDatePickerOpen] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [subsData, statsData, breakdownData, plansData] = await Promise.all([
        getSubscribers({ filter: "all", limit: 20 }).catch(() => []),
        getDashboardStats().catch(() => null),
        getDashboardSubscriptionBreakdown().catch(() => null),
        getSubscriptionPlans().catch(() => []),
      ]);
      let enrichedSubs = subsData || [];
      if (plansData && plansData.length > 0) {
        enrichedSubs = enrichedSubs.map((sub) => {
          if (!sub.status || sub.status.toLowerCase() === "free" || !sub.plan || sub.plan.toLowerCase() === "free") {
            return { ...sub, revenue: "₹0" };
          }
          const matchedPlan = plansData.find(
            (p) => p.name.trim().toLowerCase() === sub.plan.trim().toLowerCase()
          );
          if (matchedPlan) {
            const price = matchedPlan.final_price ?? matchedPlan.base_price ?? 0;
            const symbol = matchedPlan.currency === "INR" || !matchedPlan.currency ? "₹" : matchedPlan.currency;
            return {
              ...sub,
              revenue: `${symbol}${price}`,
            };
          }
          return sub;
        });
      }
      setSubscribers(enrichedSubs);
      if (statsData) setStats(statsData);
      if (breakdownData) setBreakdown(breakdownData);
      if (plansData) setAvailablePlans(plansData);
    } catch (err) {
      console.warn("Failed to load subscribers page data:", err);
      setSubscribers([]);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    loadData().finally(() => setLoading(false));
  }, [loadData]);

  const handleManualRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const currencySymbol = stats?.currency === "INR" ? "₹" : "$";
  const totalSubscribersVal = stats ? stats.totalSubscribers.current.toLocaleString() : (loading ? "—" : subscribers.length.toString());
  const growthRateVal = stats ? `${stats.totalSubscribers.growth_percentage >= 0 ? "+" : ""}${stats.totalSubscribers.growth_percentage.toFixed(1)}%` : (loading ? "—" : "0%");
  const avgRevVal = stats && stats.totalUsers.current > 0
    ? `${currencySymbol}${(stats.totalRevenue.current / stats.totalUsers.current).toFixed(2)}`
    : `${currencySymbol}0.00`;

  const subscriberStats = [
    { name: "Total Subscribers", value: totalSubscribersVal, icon: Users, color: "text-blue-600", bgColor: "bg-blue-50" },
    { name: "Growth Rate", value: growthRateVal, icon: TrendingUp, color: "text-emerald-600", bgColor: "bg-emerald-50" },
    { name: "Avg. Revenue / Member", value: avgRevVal, icon: DollarSign, color: "text-amber-600", bgColor: "bg-amber-50" },
  ];

  const planChartData = breakdown && breakdown.tiers && breakdown.tiers.length > 0
    ? breakdown.tiers.map((t) => ({
        name: t.name,
        value: t.subscribers,
        percentage: t.subscribersPercentage,
        color: t.color || "#0F172A",
        revenue: t.revenue,
      }))
    : [];

  const activeCount = [filterPlan, filterStatus].filter((v) => v !== "all").length + (filterDate ? 1 : 0);

  const resetFilters = () => { setFilterPlan("all"); setFilterStatus("all"); setFilterDate(""); setSearch(""); };

  const filtered = subscribers.filter((s) => {
    if (filterPlan !== "all" && s.plan !== filterPlan) return false;
    if (filterStatus !== "all" && s.status !== filterStatus) return false;
    if (filterDate && s.joinDate !== filterDate) return false;
    if (search && !s.name.toLowerCase().includes(search.toLowerCase()) && !s.email.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-8">
      <DatePickerDialog open={datePickerOpen} onClose={() => setDatePickerOpen(false)} value={filterDate} onChange={setFilterDate} />

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Subscribers & Members
          </h1>
          <p className="text-slate-500 mt-1 text-sm font-normal">Monitor registered mobile users, subscription tiers, and engagement status.</p>
        </div>
        <button
          onClick={handleManualRefresh}
          disabled={refreshing || loading}
          title="Refresh Data"
          className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-xs transition-all disabled:opacity-50 self-start md:self-auto"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin text-slate-900" : "text-slate-600"}`} />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-3">
        {subscriberStats.map((stat) => (
          <Card key={stat.name} className="bg-white border border-slate-200/80 shadow-xs rounded-2xl">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className={`${stat.bgColor} ${stat.color} p-3 rounded-xl`}>
                  <stat.icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-2xl lg:text-3xl font-bold text-slate-900 tracking-tight">{stat.value}</div>
                  <div className="text-sm font-semibold text-slate-700 mt-1">{stat.name}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pie chart by plan */}
      <Card className="bg-white border border-slate-200/80 shadow-xs rounded-2xl">
        <CardHeader className="border-b border-slate-100 pb-4">
          <CardTitle className="text-lg font-bold text-slate-900">Subscribers Distribution by Tier</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <ResponsiveContainer width="100%" height={220} className="max-w-xs">
              <PieChart>
                <Pie
                  data={
                    breakdown && breakdown.totalSubscribers > 0
                      ? planChartData
                      : [{ name: "Registered Members", value: 100, color: "#0F172A" }]
                  }
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  dataKey="value"
                  paddingAngle={3}
                >
                  {planChartData.map((entry, i) => (
                    <Cell key={`cell-${i}`} fill={entry.color} stroke="#FFFFFF" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v: number, name: string) => [`${v.toLocaleString()} subscribers`, name]}
                  contentStyle={{ backgroundColor: "#FFFFFF", borderColor: "#E2E8F0", borderRadius: "12px", color: "#0F172A", boxShadow: "0 4px 16px rgba(0,0,0,0.06)", fontSize: "12px" }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-3.5 w-full">
              {planChartData.map((d) => (
                <div key={d.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="h-2.5 w-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
                    <span className="text-slate-800 font-medium text-sm">{d.name} Plan</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-36 h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.max(d.percentage || 5, 2)}%`, backgroundColor: d.color }}
                      />
                    </div>
                    <span className="text-slate-800 font-mono w-16 text-right font-semibold">
                      {d.value.toLocaleString()}
                    </span>
                    <span className="text-slate-500 font-mono w-12 text-right">
                      {d.percentage !== undefined ? `${d.percentage}%` : ""}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subscriber table with working filters */}
      <Card className="bg-white border border-slate-200/80 shadow-xs rounded-2xl overflow-hidden">
        <CardHeader className="border-b border-slate-100 pb-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CardTitle className="text-lg font-bold text-slate-900">Active Subscriber Roster</CardTitle>
                <span className="text-xs bg-slate-100 text-slate-600 border border-slate-200 px-2.5 py-0.5 rounded-full font-medium">
                  {filtered.length} of {subscribers.length} showing
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input type="search" placeholder="Search subscribers..." className="pl-9 w-60 bg-white text-slate-900 placeholder:text-slate-400 border border-slate-200 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
                    value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
                <Button variant={showFilters ? "default" : "outline"} className={`gap-2 rounded-xl text-xs font-semibold shadow-xs ${
                  showFilters ? "bg-slate-900 hover:bg-slate-800 text-white" : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                }`} onClick={() => setShowFilters(!showFilters)}>
                  <SlidersHorizontal className="h-4 w-4" />
                  Filters
                  {activeCount > 0 && (
                    <span className="ml-1 bg-white text-slate-900 rounded-full text-xs font-bold px-1.5">{activeCount}</span>
                  )}
                </Button>
              </div>
            </div>

            {showFilters && (
              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <Label className="text-xs mb-1.5 block text-slate-500 font-semibold uppercase tracking-wider">Plan</Label>
                    <Select value={filterPlan} onValueChange={setFilterPlan}>
                      <SelectTrigger className="h-9 text-xs bg-white border-slate-200 text-slate-800 rounded-xl shadow-xs"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-white border-slate-200 text-slate-800 rounded-xl shadow-xl">
                        <SelectItem value="all">All Plans</SelectItem>
                        {availablePlans.map((p) => (
                          <SelectItem key={p.id} value={p.name}>{p.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block text-slate-500 font-semibold uppercase tracking-wider">Status</Label>
                    <Select value={filterStatus} onValueChange={setFilterStatus}>
                      <SelectTrigger className="h-9 text-xs bg-white border-slate-200 text-slate-800 rounded-xl shadow-xs"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-white border-slate-200 text-slate-800 rounded-xl shadow-xl">
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="Active">Active</SelectItem>
                        <SelectItem value="Free">Free</SelectItem>
                        <SelectItem value="Cancelled">Cancelled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block text-slate-500 font-semibold uppercase tracking-wider">Join Date</Label>
                    <Button variant="outline" size="sm" className="h-9 gap-1.5 text-xs w-full justify-start bg-white border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl shadow-xs"
                      onClick={() => setDatePickerOpen(true)}>
                      <Calendar className="h-3.5 w-3.5 text-slate-500" />
                      {filterDate || "Pick date"}
                      {filterDate && (
                        <X className="h-3 w-3 ml-auto text-slate-400 hover:text-rose-600"
                          onClick={(e) => { e.stopPropagation(); setFilterDate(""); }} />
                      )}
                    </Button>
                  </div>
                </div>
                {activeCount > 0 && (
                  <Button variant="ghost" size="sm" className="gap-1 text-xs text-slate-500 hover:text-slate-900 h-7" onClick={resetFilters}>
                    <X className="h-3 w-3" />Clear filters
                  </Button>
                )}
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {loading ? (
            <div className="text-center py-16 text-slate-400 flex items-center justify-center gap-2">
              <Loader2 className="h-5 w-5 animate-spin text-slate-600" /> Loading subscriber records...
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <Users className="h-10 w-10 mx-auto mb-3 text-slate-300 stroke-[1.5]" />
              <p className="font-medium text-slate-700">No subscribers match your filters</p>
              <Button variant="link" className="text-slate-900 mt-1" onClick={resetFilters}>Clear all filters</Button>
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-slate-50/80 border-b border-slate-100">
                <TableRow className="border-b border-slate-100 hover:bg-transparent">
                  <TableHead className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Subscriber</TableHead>
                  <TableHead className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Plan</TableHead>
                  <TableHead className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Status</TableHead>
                  <TableHead className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Join Date</TableHead>
                  <TableHead className="text-slate-500 text-xs font-semibold uppercase tracking-wider">Monthly Revenue</TableHead>
                  <TableHead className="text-slate-500 text-xs font-semibold uppercase tracking-wider text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((subscriber) => (
                  <TableRow key={subscriber.id} className="border-b border-slate-100 hover:bg-slate-50/60 transition-colors">
                    <TableCell className="py-3.5">
                      <div className="flex items-center gap-3">
                        {subscriber.avatarUrl ? (
                          <img
                            src={subscriber.avatarUrl}
                            alt={subscriber.name}
                            className="h-10 w-10 rounded-full object-cover border border-slate-200"
                          />
                        ) : (
                          <div className="h-10 w-10 rounded-full bg-slate-900 flex items-center justify-center text-white font-semibold text-sm shadow-xs">
                            {subscriber.name.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <div>
                          <div className="font-semibold text-sm text-slate-900">{subscriber.name}</div>
                          <div className="text-xs text-slate-500">{subscriber.email}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="py-3.5">
                      <Badge variant="outline" className={`gap-1 font-mono text-xs border ${
                        subscriber.status === "Active" ? "bg-slate-100 text-slate-800 border-slate-200" : "bg-slate-50 text-slate-600 border-slate-200"
                      }`}>
                        {subscriber.status === "Active" && <Crown className="h-3 w-3 text-slate-700" />}
                        {subscriber.plan}
                      </Badge>
                    </TableCell>
                    <TableCell className="py-3.5">
                      <Badge variant="outline" className={`font-mono text-xs border ${
                        subscriber.status === "Active" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-slate-100 text-slate-600 border-slate-200"
                      }`}>
                        {subscriber.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="py-3.5 text-slate-500 font-mono text-xs">{subscriber.joinDate}</TableCell>
                    <TableCell className="py-3.5 font-mono text-xs font-bold text-slate-900">{subscriber.revenue}</TableCell>
                    <TableCell className="py-3.5 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg"><MoreVertical className="h-4 w-4" /></Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-white border-slate-200 text-slate-700 shadow-xl rounded-xl">
                          <DropdownMenuItem
                            className="hover:bg-slate-50 focus:bg-slate-50 cursor-pointer"
                            onClick={() => {
                              if (subscriber.email && !subscriber.email.includes("No email")) {
                                window.location.href = `mailto:${subscriber.email}`;
                              } else {
                                toast.info("No email address registered for this account.");
                              }
                            }}
                          >
                            <Mail className="mr-2 h-4 w-4 text-slate-500" />Send Email
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="hover:bg-slate-50 focus:bg-slate-50 cursor-pointer"
                            onClick={() => toast.info("Navigate to Subscription Plans to manage subscriber tier entitlements.")}
                          >
                            <Crown className="mr-2 h-4 w-4 text-slate-500" />Change Plan
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-rose-600 hover:bg-rose-50 focus:bg-rose-50 cursor-pointer"
                            onClick={() => toast.info(`Account status for ${subscriber.name} is managed in Security & Team Access settings.`)}
                          >
                            <UserX className="mr-2 h-4 w-4" />Suspend Account
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

