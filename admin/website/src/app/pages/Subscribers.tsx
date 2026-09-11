import { useState, useEffect, useCallback } from "react";
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
      <DialogContent className="max-w-xs">
        <DialogHeader>
          <DialogTitle>Filter by Date</DialogTitle>
          <DialogDescription>Show subscribers who joined on this date</DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <Input type="date" value={local} onChange={(e) => setLocal(e.target.value)} />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { onChange(""); setLocal(""); onClose(); }}>Clear</Button>
          <Button onClick={() => { onChange(local); onClose(); }}>Apply</Button>
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
      setSubscribers(subsData || []);
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
    { name: "Total Subscribers", value: totalSubscribersVal, icon: Users, color: "text-blue-400", bgColor: "bg-blue-500/10" },
    { name: "Growth Rate", value: growthRateVal, icon: TrendingUp, color: "text-emerald-400", bgColor: "bg-emerald-500/10" },
    { name: "Avg. Revenue / Member", value: avgRevVal, icon: DollarSign, color: "text-amber-400", bgColor: "bg-amber-500/10" },
  ];

  const planChartData = breakdown && breakdown.tiers && breakdown.tiers.length > 0
    ? breakdown.tiers.map((t) => ({
        name: t.name,
        value: t.subscribers,
        percentage: t.subscribersPercentage,
        color: t.color || "#8b5cf6",
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

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            Subscribers & Members
            <span className="text-xs bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 px-2.5 py-1 rounded-full font-mono font-medium flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              LIVE FASTAPI
            </span>
          </h1>
          <p className="text-slate-400 mt-1 text-sm">Monitor registered mobile users, subscription tiers, and engagement status.</p>
        </div>
        <button
          onClick={handleManualRefresh}
          disabled={refreshing || loading}
          title="Refresh Data"
          className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white transition-all disabled:opacity-50 self-start md:self-auto"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin text-purple-400" : ""}`} />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-5 md:grid-cols-3">
        {subscriberStats.map((stat) => (
          <Card key={stat.name} className="bg-slate-900/60 backdrop-blur-xl border-slate-800/80 shadow-xl hover:border-purple-500/30 transition-all">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className={`${stat.bgColor} ${stat.color} p-3.5 rounded-xl border border-white/5`}>
                  <stat.icon className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white tracking-tight">{stat.value}</div>
                  <div className="text-xs font-medium text-slate-400 mt-0.5">{stat.name}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Pie chart by plan */}
      <Card className="bg-slate-900/60 backdrop-blur-xl border-slate-800/80 shadow-xl">
        <CardHeader className="border-b border-slate-800/60 pb-4">
          <CardTitle className="text-lg font-semibold text-white">Subscribers Distribution by Tier</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row items-center gap-8">
            <ResponsiveContainer width="100%" height={220} className="max-w-xs">
              <PieChart>
                <Pie
                  data={
                    breakdown && breakdown.totalSubscribers > 0
                      ? planChartData
                      : [{ name: "Registered Members", value: 100, color: "#6366f1" }]
                  }
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={90}
                  dataKey="value"
                  paddingAngle={3}
                >
                  {planChartData.map((entry, i) => (
                    <Cell key={`cell-${i}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v: number, name: string) => [`${v.toLocaleString()} subscribers`, name]}
                  contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", borderRadius: "8px", color: "#fff" }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-3.5 w-full">
              {planChartData.map((d) => (
                <div key={d.name} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="h-3 w-3 rounded-full flex-shrink-0" style={{ backgroundColor: d.color }} />
                    <span className="text-slate-200 font-medium text-sm">{d.name} Plan</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-36 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${Math.max(d.percentage || 5, 2)}%`, backgroundColor: d.color }}
                      />
                    </div>
                    <span className="text-slate-300 font-mono w-16 text-right font-semibold">
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
      <Card className="bg-slate-900/60 backdrop-blur-xl border-slate-800/80 shadow-xl overflow-hidden">
        <CardHeader className="border-b border-slate-800/60 pb-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CardTitle className="text-lg font-semibold text-white">Active Subscriber Roster</CardTitle>
                <span className="text-xs bg-slate-800 text-slate-400 border border-slate-700 px-2.5 py-0.5 rounded-full">
                  {filtered.length} of {subscribers.length} showing
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <Input type="search" placeholder="Search subscribers..." className="pl-9 w-60 bg-slate-950 text-slate-100 placeholder:text-slate-500 border border-slate-800 focus:border-purple-500/50 rounded-xl"
                    value={search} onChange={(e) => setSearch(e.target.value)} />
                </div>
                <Button variant={showFilters ? "default" : "outline"} className={`gap-2 rounded-xl text-xs font-semibold ${
                  showFilters ? "bg-purple-600 hover:bg-purple-500 text-white" : "bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800"
                }`} onClick={() => setShowFilters(!showFilters)}>
                  <SlidersHorizontal className="h-4 w-4" />
                  Filters
                  {activeCount > 0 && (
                    <span className="ml-1 bg-white text-purple-900 rounded-full text-xs font-bold px-1.5">{activeCount}</span>
                  )}
                </Button>
              </div>
            </div>

            {showFilters && (
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4">
                <div className="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <Label className="text-xs mb-1.5 block text-slate-400">Plan</Label>
                    <Select value={filterPlan} onValueChange={setFilterPlan}>
                      <SelectTrigger className="h-9 text-xs bg-slate-900 border-slate-800 text-slate-200"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                        <SelectItem value="all">All Plans</SelectItem>
                        {availablePlans.map((p) => (
                          <SelectItem key={p.id} value={p.name}>{p.name}</SelectItem>
                        ))}
                        {availablePlans.length === 0 && (
                          <>
                            <SelectItem value="Premium">Premium</SelectItem>
                            <SelectItem value="Basic">Basic</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block text-slate-400">Status</Label>
                    <Select value={filterStatus} onValueChange={setFilterStatus}>
                      <SelectTrigger className="h-9 text-xs bg-slate-900 border-slate-800 text-slate-200"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-slate-200">
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="Active">Active</SelectItem>
                        <SelectItem value="Free">Free</SelectItem>
                        <SelectItem value="Cancelled">Cancelled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block text-slate-400">Join Date</Label>
                    <Button variant="outline" size="sm" className="h-9 gap-1.5 text-xs w-full justify-start bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800"
                      onClick={() => setDatePickerOpen(true)}>
                      <Calendar className="h-3.5 w-3.5 text-purple-400" />
                      {filterDate || "Pick date"}
                      {filterDate && (
                        <X className="h-3 w-3 ml-auto text-slate-500 hover:text-rose-400"
                          onClick={(e) => { e.stopPropagation(); setFilterDate(""); }} />
                      )}
                    </Button>
                  </div>
                </div>
                {activeCount > 0 && (
                  <Button variant="ghost" size="sm" className="gap-1 text-xs text-slate-400 hover:text-white h-7" onClick={resetFilters}>
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
              <Loader2 className="h-5 w-5 animate-spin text-purple-400" /> Loading subscriber records...
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-16 text-slate-500">
              <Users className="h-10 w-10 mx-auto mb-3 opacity-30 text-purple-400" />
              <p className="font-medium text-slate-300">No subscribers match your filters</p>
              <Button variant="link" className="text-purple-400 mt-1" onClick={resetFilters}>Clear all filters</Button>
            </div>
          ) : (
            <Table>
              <TableHeader className="bg-slate-950/80 border-b border-slate-800">
                <TableRow className="border-slate-800/80 hover:bg-transparent">
                  <TableHead className="text-slate-400 text-xs uppercase font-mono">Subscriber</TableHead>
                  <TableHead className="text-slate-400 text-xs uppercase font-mono">Plan</TableHead>
                  <TableHead className="text-slate-400 text-xs uppercase font-mono">Status</TableHead>
                  <TableHead className="text-slate-400 text-xs uppercase font-mono">Join Date</TableHead>
                  <TableHead className="text-slate-400 text-xs uppercase font-mono">Monthly Revenue</TableHead>
                  <TableHead className="text-slate-400 text-xs uppercase font-mono text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((subscriber) => (
                  <TableRow key={subscriber.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                    <TableCell className="py-3.5">
                      <div className="flex items-center gap-3">
                        {subscriber.avatarUrl ? (
                          <img
                            src={subscriber.avatarUrl}
                            alt={subscriber.name}
                            className="h-10 w-10 rounded-full object-cover border border-purple-500/20"
                          />
                        ) : (
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-500 via-indigo-500 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-md">
                            {subscriber.name.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <div>
                          <div className="font-semibold text-sm text-slate-100">{subscriber.name}</div>
                          <div className="text-xs text-slate-400 font-mono">{subscriber.email}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="py-3.5">
                      <Badge variant="outline" className={`gap-1 font-mono text-xs border ${
                        subscriber.status === "Active" ? "bg-purple-500/10 text-purple-300 border-purple-500/30" : "bg-slate-800 text-slate-300 border-slate-700"
                      }`}>
                        {subscriber.status === "Active" && <Crown className="h-3 w-3 text-purple-400" />}
                        {subscriber.plan}
                      </Badge>
                    </TableCell>
                    <TableCell className="py-3.5">
                      <Badge variant="outline" className={`font-mono text-xs border ${
                        subscriber.status === "Active" ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30" : "bg-slate-800 text-slate-400 border-slate-700"
                      }`}>
                        {subscriber.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="py-3.5 text-slate-400 font-mono text-xs">{subscriber.joinDate}</TableCell>
                    <TableCell className="py-3.5 font-mono text-xs font-bold text-emerald-400">{subscriber.revenue}</TableCell>
                    <TableCell className="py-3.5 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"><MoreVertical className="h-4 w-4" /></Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="bg-slate-900 border-slate-800 text-slate-200">
                          <DropdownMenuItem className="hover:bg-slate-800 focus:bg-slate-800 cursor-pointer"><Mail className="mr-2 h-4 w-4 text-purple-400" />Send Email</DropdownMenuItem>
                          <DropdownMenuItem className="hover:bg-slate-800 focus:bg-slate-800 cursor-pointer"><Crown className="mr-2 h-4 w-4 text-amber-400" />Change Plan</DropdownMenuItem>
                          <DropdownMenuItem className="text-rose-400 hover:bg-slate-800 focus:bg-slate-800 cursor-pointer"><UserX className="mr-2 h-4 w-4" />Suspend Account</DropdownMenuItem>
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

