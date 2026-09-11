import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { DollarSign, TrendingUp, TrendingDown, CreditCard, Download, Calendar, Loader2, RefreshCw } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../components/ui/table";
import { Badge } from "../components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  getDashboardStats,
  getDashboardAnalytics,
  getDashboardSubscriptionBreakdown,
  getDashboardRecentActivity,
  ApiDashboardStats,
  ApiAnalytics,
  ApiSubscriptionBreakdown,
  ApiRecentActivityUser,
} from "../services/apiService";

export default function Revenue() {
  const [selectedRange, setSelectedRange] = useState<string>("30");
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<ApiDashboardStats | null>(null);
  const [analytics, setAnalytics] = useState<ApiAnalytics | null>(null);
  const [breakdown, setBreakdown] = useState<ApiSubscriptionBreakdown | null>(null);
  const [recentTransactions, setRecentTransactions] = useState<ApiRecentActivityUser[]>([]);

  const apiRange = useMemo(() => {
    switch (selectedRange) {
      case "7":
        return "7d";
      case "30":
        return "30d";
      case "90":
        return "90d";
      case "365":
        return "12m";
      default:
        return "30d";
    }
  }, [selectedRange]);

  const currencySymbol = useMemo(() => {
    if (!stats?.currency) return "₹";
    if (stats.currency.toUpperCase() === "USD") return "$";
    if (stats.currency.toUpperCase() === "EUR") return "€";
    if (stats.currency.toUpperCase() === "GBP") return "£";
    return "₹";
  }, [stats?.currency]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, analyticsRes, breakdownRes, activityRes] = await Promise.all([
        getDashboardStats({ range: apiRange }).catch(() => null),
        getDashboardAnalytics({ range: apiRange, interval: selectedRange === "365" ? "month" : "week" }).catch(() => null),
        getDashboardSubscriptionBreakdown({ range: apiRange }).catch(() => null),
        getDashboardRecentActivity({ filter: "subscribers", limit: 10 }).catch(() => ({ items: [] })),
      ]);

      setStats(statsRes);
      setAnalytics(analyticsRes);
      setBreakdown(breakdownRes);
      setRecentTransactions(activityRes?.items || []);
    } catch (err) {
      console.warn("Failed to load revenue data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [apiRange]);

  const nextPayoutDate = useMemo(() => {
    const d = new Date();
    d.setMonth(d.getMonth() + 1);
    d.setDate(1);
    return d.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
  }, []);

  const revenueStats = [
    {
      name: "Total Revenue",
      value: stats ? `${currencySymbol}${stats.totalRevenue.current.toLocaleString()}` : `${currencySymbol}0`,
      change: stats
        ? `${stats.totalRevenue.growth_percentage >= 0 ? "+" : ""}${stats.totalRevenue.growth_percentage.toFixed(1)}%`
        : "0%",
      trend: stats && stats.totalRevenue.growth_percentage >= 0 ? "up" : "down",
      icon: DollarSign,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10 border border-emerald-500/20",
    },
    {
      name: "Period Growth",
      value: stats ? `${stats.totalRevenue.growth_percentage >= 0 ? "+" : ""}${stats.totalRevenue.growth_percentage.toFixed(1)}%` : "0%",
      change: stats?.totalRevenue.previous ? `vs ${currencySymbol}${stats.totalRevenue.previous.toLocaleString()} prev` : "No prior period",
      trend: stats && stats.totalRevenue.growth_percentage >= 0 ? "up" : "down",
      icon: TrendingUp,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10 border border-blue-500/20",
    },
    {
      name: "Active Subscriptions",
      value: stats ? stats.totalSubscribers.current.toLocaleString() : "0",
      change: stats
        ? `${stats.totalSubscribers.growth_percentage >= 0 ? "+" : ""}${stats.totalSubscribers.growth_percentage.toFixed(1)}%`
        : "0%",
      trend: stats && stats.totalSubscribers.growth_percentage >= 0 ? "up" : "down",
      icon: CreditCard,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10 border border-purple-500/20",
    },
    {
      name: "Avg. Revenue / User",
      value: stats && stats.totalUsers.current > 0
        ? `${currencySymbol}${(stats.totalRevenue.current / stats.totalUsers.current).toFixed(2)}`
        : `${currencySymbol}0.00`,
      change: stats ? `${stats.totalUsers.current.toLocaleString()} total users` : "0 users",
      trend: "up",
      icon: DollarSign,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10 border border-amber-500/20",
    },
  ];

  const handleExport = () => {
    if (!analytics?.dataPoints || analytics.dataPoints.length === 0) {
      alert("No revenue data points available to export.");
      return;
    }
    const headers = ["Date", "Period", "Revenue", "Subscribers", "Active Users"];
    const rows = analytics.dataPoints.map((p) => [
      p.date,
      p.label,
      p.revenue,
      p.subscribers,
      p.users,
    ]);
    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `revenue_${apiRange}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Revenue & Monetization</h1>
          <p className="text-slate-300 mt-1 font-medium">Track your live earnings and subscription financial performance</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedRange} onValueChange={(v) => setSelectedRange(v)}>
            <SelectTrigger className="w-40 bg-slate-950/80 border-slate-800 text-slate-100">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
              <SelectItem value="365">Last year</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="icon"
            onClick={loadData}
            disabled={loading}
            className="border-slate-800 bg-slate-900 text-slate-200 hover:bg-slate-800"
            title="Refresh Data"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-purple-400" : "text-slate-300"}`} />
          </Button>
          <Button
            variant="outline"
            className="gap-2 border-slate-800 bg-slate-900 text-slate-200 hover:bg-slate-800"
            onClick={handleExport}
            disabled={!analytics?.dataPoints || analytics.dataPoints.length === 0}
          >
            <Download className="h-4 w-4 text-purple-400" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Revenue Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {revenueStats.map((stat) => (
          <Card key={stat.name} className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className={`${stat.bgColor} ${stat.color} p-3 rounded-xl`}>
                  <stat.icon className="h-6 w-6" />
                </div>
                <div
                  className={`flex items-center gap-1 text-sm font-semibold ${
                    stat.trend === "up" ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {stat.trend === "up" ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {stat.change}
                </div>
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-white">
                  {loading && !stats ? (
                    <span className="inline-block w-20 h-7 bg-slate-800 animate-pulse rounded" />
                  ) : (
                    stat.value
                  )}
                </div>
                <div className="text-sm text-slate-400 font-medium mt-0.5">{stat.name}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Revenue Timeline Chart */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <CardHeader className="border-b border-slate-800 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white">Revenue Timeline Breakdown</CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">Earnings progression for selected period</p>
          </div>
          {loading && <Loader2 className="h-4 w-4 animate-spin text-purple-400" />}
        </CardHeader>
        <CardContent className="pt-6">
          {analytics?.dataPoints && analytics.dataPoints.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={analytics.dataPoints}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="label" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  formatter={(value: any, name: string) => [
                    name === "Revenue" ? `${currencySymbol}${Number(value).toLocaleString()}` : value,
                    name,
                  ]}
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "12px",
                    color: "#f8fafc",
                  }}
                />
                <Legend wrapperStyle={{ color: "#cbd5e1" }} />
                <Bar dataKey="revenue" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Revenue" />
                <Bar dataKey="subscribers" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Subscribers" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[350px] flex flex-col items-center justify-center text-slate-500">
              {loading ? (
                <Loader2 className="h-8 w-8 animate-spin text-purple-500 mb-2" />
              ) : (
                <>
                  <DollarSign className="h-10 w-10 mb-2 stroke-[1.5]" />
                  <p className="text-sm">No revenue data recorded for this period yet.</p>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Revenue by Plan */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-slate-800">
            <CardTitle className="text-white">Revenue by Plan Type</CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">Tier distribution and monetary contribution</p>
          </CardHeader>
          <CardContent className="pt-6">
            {breakdown?.tiers && breakdown.tiers.length > 0 ? (
              <div className="space-y-4">
                {breakdown.tiers.map((item) => (
                  <div key={item.planId}>
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <div className="font-semibold text-slate-200 flex items-center gap-2">
                          {item.name}
                          {item.badgeText && (
                            <span className="text-[10px] bg-purple-950/80 text-purple-300 border border-purple-800/60 px-1.5 py-0.5 rounded-full font-medium">
                              {item.badgeText}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-400 font-medium">
                          {item.subscribers.toLocaleString()} subscribers
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-emerald-400">
                          {currencySymbol}{item.revenue.toLocaleString()}
                        </div>
                        <div className="text-xs text-slate-400 font-medium">
                          {item.revenuePercentage.toFixed(1)}% of total
                        </div>
                      </div>
                    </div>
                    <div className="h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(Math.max(item.revenuePercentage, 0), 100)}%`,
                          backgroundColor: item.color || "#8b5cf6",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-[200px] flex flex-col items-center justify-center text-slate-500">
                <CreditCard className="h-8 w-8 mb-2 stroke-[1.5]" />
                <p className="text-sm">No subscription tiers data recorded.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Payout Information */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-slate-800">
            <CardTitle className="text-white">Earnings & Settlement</CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">Estimated payout for current cycle</p>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="space-y-4">
              <div className="p-5 bg-gradient-to-br from-purple-950/40 to-blue-950/40 rounded-xl border border-purple-500/20">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-300 font-medium">Captured Period Earnings</span>
                  <Calendar className="h-4 w-4 text-purple-400" />
                </div>
                <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-cyan-300 mb-1">
                  {currencySymbol}{stats ? stats.totalRevenue.current.toLocaleString() : "0"}
                </div>
                <div className="text-xs text-slate-400 font-medium">
                  Next scheduled settlement on {nextPayoutDate}
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <div className="flex items-center justify-between text-sm font-semibold">
                  <span className="text-slate-300">Active Subscribers Balance</span>
                  <span className="text-emerald-400 font-mono">
                    {currencySymbol}{stats ? stats.totalRevenue.current.toLocaleString() : "0"}
                  </span>
                </div>
              </div>

              <div className="text-xs text-slate-400 space-y-1">
                <p>• Payouts are processed on the 1st of each calendar month.</p>
                <p>• Direct bank transfers require verified payment gateway credentials.</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <CardHeader className="border-b border-slate-800">
          <CardTitle className="text-white">Recent Subscriber Conversions</CardTitle>
          <p className="text-xs text-slate-400 mt-0.5">Live subscription activations from mobile users</p>
        </CardHeader>
        <CardContent className="p-0">
          {recentTransactions.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="border-b border-slate-800 hover:bg-transparent">
                  <TableHead className="text-slate-400">Account ID</TableHead>
                  <TableHead className="text-slate-400">Subscriber</TableHead>
                  <TableHead className="text-slate-400">Plan</TableHead>
                  <TableHead className="text-slate-400">Status</TableHead>
                  <TableHead className="text-slate-400">Subscribed At</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentTransactions.map((transaction) => (
                  <TableRow key={transaction.id} className="border-b border-slate-800/60 hover:bg-slate-800/40">
                    <TableCell className="font-mono text-xs text-purple-400">
                      SUB-{transaction.id.toString().padStart(5, "0")}
                    </TableCell>
                    <TableCell>
                      <div className="font-medium text-slate-200">
                        {transaction.name || "Subscriber"}
                      </div>
                      <div className="text-xs text-slate-400">
                        {transaction.email || "Registered Account"}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-purple-800/60 bg-purple-950/40 text-purple-300 font-normal">
                        {transaction.planName || "Active Plan"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={transaction.isPaid ? "default" : "secondary"}
                        className={
                          transaction.isPaid
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                            : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                        }
                      >
                        {transaction.isPaid ? "Active Paid" : "Free Member"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {transaction.subscribedAt
                        ? new Date(transaction.subscribedAt).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })
                        : new Date(transaction.joinedAt).toLocaleDateString("en-US", {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="py-12 flex flex-col items-center justify-center text-slate-500">
              {loading ? (
                <Loader2 className="h-8 w-8 animate-spin text-purple-500 mb-2" />
              ) : (
                <>
                  <CreditCard className="h-10 w-10 mb-2 stroke-[1.5]" />
                  <p className="text-sm">No subscriber conversions recorded yet.</p>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
