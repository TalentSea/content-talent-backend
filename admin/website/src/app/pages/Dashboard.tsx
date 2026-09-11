import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import {
  ArrowUpRight,
  ArrowDownRight,
  Users,
  Video,
  DollarSign,
  Eye,
  UserCheck,
  Loader2,
  RefreshCw,
  PlaySquare,
  Clock,
  Sparkles,
  Layers,
} from "lucide-react";
import {
  ComposedChart,
  Line,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  getDashboardStats,
  getDashboardAnalytics,
  getDashboardSubscriptionBreakdown,
  getDashboardRecentActivity,
  getVideos,
  ApiDashboardStats,
  ApiAnalytics,
  ApiSubscriptionBreakdown,
  ApiRecentActivityUser,
  ApiVideo,
} from "../services/apiService";

const RANGES = [
  { label: "7 Days", value: "7d" },
  { label: "30 Days", value: "30d" },
  { label: "90 Days", value: "90d" },
  { label: "12 Months", value: "12m" },
];

const RECENT_FILTERS: Array<{ label: string; value: "all" | "subscribers" | "users" }> = [
  { label: "All Activity", value: "all" },
  { label: "Subscribers", value: "subscribers" },
  { label: "Signups", value: "users" },
];

function formatNumber(num: number): string {
  if (isNaN(num)) return "0";
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + "M";
  if (num >= 1_000) return (num / 1_000).toFixed(1) + "K";
  return num.toLocaleString();
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return "Recently";
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export default function Dashboard() {
  const [range, setRange] = useState<string>("30d");
  const [recentFilter, setRecentFilter] = useState<"all" | "subscribers" | "users">("all");

  const [stats, setStats] = useState<ApiDashboardStats | null>(null);
  const [analytics, setAnalytics] = useState<ApiAnalytics | null>(null);
  const [breakdown, setBreakdown] = useState<ApiSubscriptionBreakdown | null>(null);
  const [recentActivity, setRecentActivity] = useState<ApiRecentActivityUser[]>([]);
  const [topVideos, setTopVideos] = useState<ApiVideo[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [activityLoading, setActivityLoading] = useState<boolean>(false);

  // Fetch Dashboard Stats, Analytics, and Subscription Breakdown
  const fetchDashboardMetrics = useCallback(async (selectedRange: string) => {
    try {
      const [statsRes, analyticsRes, breakdownRes] = await Promise.all([
        getDashboardStats({ range: selectedRange }).catch((e) => {
          console.error("Stats API error:", e);
          return null;
        }),
        getDashboardAnalytics({ range: selectedRange }).catch((e) => {
          console.error("Analytics API error:", e);
          return null;
        }),
        getDashboardSubscriptionBreakdown({ range: selectedRange }).catch((e) => {
          console.error("Breakdown API error:", e);
          return null;
        }),
      ]);
      if (statsRes) setStats(statsRes);
      if (analyticsRes) setAnalytics(analyticsRes);
      if (breakdownRes) setBreakdown(breakdownRes);
    } catch (err) {
      console.error("Failed to fetch dashboard metrics:", err);
    }
  }, []);

  // Fetch Recent Activity based on selected filter (Safe Array Extraction)
  const fetchRecentActivity = useCallback(async (filter: "all" | "subscribers" | "users") => {
    setActivityLoading(true);
    try {
      const res = await getDashboardRecentActivity({ filter, limit: 6 });
      // Safeguard against object envelope { items: [...] } vs direct array
      const items = Array.isArray(res) ? res : Array.isArray(res?.items) ? res.items : [];
      setRecentActivity(items);
    } catch (err) {
      console.error("Failed to fetch recent activity:", err);
      setRecentActivity([]);
    } finally {
      setActivityLoading(false);
    }
  }, []);

  // Fetch Top Performing Videos
  const fetchTopVideos = useCallback(async () => {
    try {
      const res = await getVideos({ limit: 4, sort: "views" });
      const rawList = Array.isArray(res?.data) ? res.data : Array.isArray(res) ? res : [];
      const sorted = [...rawList].sort((a, b) => {
        const vA = typeof a.views === "number" ? a.views : parseInt(String(a.views || 0), 10) || 0;
        const vB = typeof b.views === "number" ? b.views : parseInt(String(b.views || 0), 10) || 0;
        return vB - vA;
      });
      setTopVideos(sorted.slice(0, 4));
    } catch (err) {
      console.error("Failed to fetch top videos:", err);
      setTopVideos([]);
    }
  }, []);

  // Initial and range-change loader
  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchDashboardMetrics(range),
      fetchRecentActivity(recentFilter),
      fetchTopVideos(),
    ]).finally(() => {
      setLoading(false);
    });
  }, [range, fetchDashboardMetrics, fetchRecentActivity, fetchTopVideos]);

  // When recent filter changes
  const handleFilterChange = (filter: "all" | "subscribers" | "users") => {
    setRecentFilter(filter);
    fetchRecentActivity(filter);
  };

  // Manual refresh
  const handleManualRefresh = async () => {
    setRefreshing(true);
    await Promise.all([
      fetchDashboardMetrics(range),
      fetchRecentActivity(recentFilter),
      fetchTopVideos(),
    ]);
    setRefreshing(false);
  };

  const currencySymbol = stats?.currency === "INR" ? "₹" : "$";

  // KPI cards aligned with FastAPI GrowthMetric schema
  const kpiCards = [
    {
      name: "Total Users",
      value: stats ? stats.totalUsers.current.toLocaleString() : "—",
      change: stats
        ? `${stats.totalUsers.growth_percentage >= 0 ? "+" : ""}${stats.totalUsers.growth_percentage.toFixed(1)}%`
        : "—",
      trend: stats && stats.totalUsers.growth_percentage >= 0 ? ("up" as const) : ("down" as const),
      icon: UserCheck,
      color: "text-teal-400",
      bgColor: "bg-teal-500/10",
      subtext: stats ? `Prior: ${stats.totalUsers.previous.toLocaleString()}` : "Active registered accounts",
    },
    {
      name: "Total Subscribers",
      value: stats ? stats.totalSubscribers.current.toLocaleString() : "—",
      change: stats
        ? `${stats.totalSubscribers.growth_percentage >= 0 ? "+" : ""}${stats.totalSubscribers.growth_percentage.toFixed(1)}%`
        : "—",
      trend: stats && stats.totalSubscribers.growth_percentage >= 0 ? ("up" as const) : ("down" as const),
      icon: Users,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
      subtext: stats ? `Prior: ${stats.totalSubscribers.previous.toLocaleString()}` : "Paid subscription plans",
    },
    {
      name: "Total Content",
      value: stats ? stats.totalContent.total.toLocaleString() : "—",
      change: stats?.totalContent
        ? `${stats.totalContent.published} pub • ${stats.totalContent.drafts} drafts • +${stats.totalContent.recently_added} new`
        : "Catalog inventory",
      trend: "up" as const,
      icon: Video,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10",
      subtext: "Videos & catalog assets",
    },
    {
      name: "Total Revenue",
      value: stats
        ? `${currencySymbol}${stats.totalRevenue.current.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
        : "—",
      change: stats
        ? `${stats.totalRevenue.growth_percentage >= 0 ? "+" : ""}${stats.totalRevenue.growth_percentage.toFixed(1)}%`
        : "—",
      trend: stats && stats.totalRevenue.growth_percentage >= 0 ? ("up" as const) : ("down" as const),
      icon: DollarSign,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      subtext: stats
        ? `Prior: ${currencySymbol}${stats.totalRevenue.previous.toLocaleString()}`
        : "Gross captured revenue",
    },
    {
      name: "Total Views",
      value: stats ? formatNumber(stats.totalViews.current) : "—",
      change: stats
        ? `${stats.totalViews.growth_percentage >= 0 ? "+" : ""}${stats.totalViews.growth_percentage.toFixed(1)}%`
        : "—",
      trend: stats && stats.totalViews.growth_percentage >= 0 ? ("up" as const) : ("down" as const),
      icon: Eye,
      color: "text-amber-400",
      bgColor: "bg-amber-500/10",
      subtext: stats ? `Prior: ${formatNumber(stats.totalViews.previous)}` : "Platform stream telemetry",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-3">
            Studio Dashboard
            <span className="text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2.5 py-1 rounded-full font-mono font-medium flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              LIVE FASTAPI
            </span>
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Real-time analytics, subscriber trends, and live content metrics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Time range selector */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-1 flex items-center gap-1">
            {RANGES.map((r) => (
              <button
                key={r.value}
                onClick={() => setRange(r.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  range === r.value
                    ? "bg-purple-600 text-white shadow-md shadow-purple-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          {/* Refresh Button */}
          <button
            onClick={handleManualRefresh}
            disabled={refreshing || loading}
            title="Refresh Data"
            className="p-2.5 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white transition-all disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin text-purple-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-5">
        {kpiCards.map((stat) => (
          <Card
            key={stat.name}
            className="bg-slate-900/60 backdrop-blur-xl border-slate-800/80 hover:border-purple-500/40 transition-all duration-300 shadow-xl hover:shadow-2xl hover:shadow-purple-500/5 group"
          >
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <div
                  className={`${stat.bgColor} p-3 rounded-xl border border-white/5 group-hover:scale-105 transition-transform duration-200`}
                >
                  <stat.icon className={`h-5 w-5 ${stat.color}`} />
                </div>
                {stat.name === "Total Content" ? (
                  <span className="text-[11px] font-mono text-purple-300/80 bg-purple-500/10 px-2 py-0.5 rounded-md border border-purple-500/20">
                    Live
                  </span>
                ) : (
                  <div
                    className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-lg ${
                      stat.trend === "up"
                        ? "text-emerald-400 bg-emerald-500/10 border border-emerald-500/20"
                        : "text-rose-400 bg-rose-500/10 border border-rose-500/20"
                    }`}
                  >
                    {stat.trend === "up" ? (
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    ) : (
                      <ArrowDownRight className="h-3.5 w-3.5" />
                    )}
                    {stat.change}
                  </div>
                )}
              </div>
              <div className="mt-4">
                <div className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
                  {loading && !stats ? (
                    <div className="h-7 w-20 bg-slate-800 animate-pulse rounded"></div>
                  ) : (
                    stat.value
                  )}
                </div>
                <div className="text-xs font-medium text-slate-400 mt-1">{stat.name}</div>
                {stat.subtext && (
                  <div className="text-[11px] text-slate-500 font-mono mt-1 truncate">
                    {stat.subtext}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Analytics Charts Row */}
      <div className="grid gap-6 lg:grid-cols-7">
        {/* Revenue & Subscriber Analytics Chart */}
        <Card className="lg:col-span-4 bg-slate-900/60 backdrop-blur-xl border-slate-800/80 shadow-xl">
          <CardHeader className="border-b border-slate-800/60 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                  Audience & Content Telemetry
                </CardTitle>
                <div className="text-xs text-slate-400 mt-0.5">
                  Chronological performance across the selected {range.toUpperCase()} window
                </div>
              </div>
              {stats && (
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-emerald-400 font-semibold">
                    {currencySymbol}{stats.totalRevenue.current.toLocaleString()}
                    <span className="text-slate-500 font-normal ml-1">rev</span>
                  </span>
                  <span className="text-blue-400 font-semibold">
                    {stats.totalViews.current.toLocaleString()}
                    <span className="text-slate-500 font-normal ml-1">views</span>
                  </span>
                  <span className="text-teal-400 font-semibold">
                    +{stats.totalUsers.current.toLocaleString()}
                    <span className="text-slate-500 font-normal ml-1">users</span>
                  </span>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {loading && !analytics ? (
              <div className="h-[300px] flex items-center justify-center text-slate-400 gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-purple-400" />
                Loading analytics telemetry...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <ComposedChart data={analytics?.dataPoints || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.6} />
                  <XAxis
                    dataKey="label"
                    stroke="#64748b"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <YAxis
                    yAxisId="left"
                    stroke="#64748b"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <YAxis
                    yAxisId="right"
                    orientation="right"
                    stroke="#64748b"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "12px",
                      color: "#f8fafc",
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: "10px" }} />
                  <Bar
                    yAxisId="left"
                    dataKey="views"
                    fill="#3b82f6"
                    name="Views"
                    radius={[4, 4, 0, 0]}
                    opacity={0.85}
                  />
                  <Line
                    yAxisId="left"
                    type="monotone"
                    dataKey="users"
                    stroke="#10b981"
                    strokeWidth={2}
                    name="Signups"
                    dot={{ fill: "#10b981", r: 3 }}
                  />
                  <Line
                    yAxisId="right"
                    type="monotone"
                    dataKey="revenue"
                    stroke="#a855f7"
                    strokeWidth={3}
                    name={`Revenue (${currencySymbol})`}
                    dot={{ fill: "#a855f7", r: 3 }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Subscription Tier Distribution */}
        <Card className="lg:col-span-3 bg-slate-900/60 backdrop-blur-xl border-slate-800/80 shadow-xl">
          <CardHeader className="border-b border-slate-800/60 pb-4">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold text-white">
                Subscription Tier Distribution
              </CardTitle>
              {breakdown && (
                <span className="text-xs bg-purple-500/10 text-purple-300 border border-purple-500/20 px-2.5 py-0.5 rounded-full font-mono">
                  {breakdown.totalSubscribers} subscribers
                </span>
              )}
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            {loading && !breakdown ? (
              <div className="h-[260px] flex items-center justify-center text-slate-400 gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-purple-400" />
                Loading tier breakdown...
              </div>
            ) : breakdown && breakdown.tiers && breakdown.tiers.length > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={170}>
                  <PieChart>
                    <Pie
                      data={
                        breakdown.totalSubscribers > 0
                          ? breakdown.tiers
                          : [{ name: "Registered Free Accounts", subscribersPercentage: 100, color: "#6366f1" }]
                      }
                      cx="50%"
                      cy="50%"
                      innerRadius={52}
                      outerRadius={80}
                      dataKey="subscribersPercentage"
                      paddingAngle={3}
                    >
                      {breakdown.tiers.map((entry, index) => (
                        <Cell
                          key={`cell-${entry.planId || index}`}
                          fill={entry.color || "#8b5cf6"}
                          stroke="#0f172a"
                          strokeWidth={2}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(v, name, item) => [
                        `${v}% (${item?.payload?.subscribers ?? 0} subs)`,
                        item?.payload?.name || name,
                      ]}
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "8px",
                        color: "#fff",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>

                <div className="mt-3 space-y-2.5">
                  {breakdown.tiers.map((t) => (
                    <div key={t.planId || t.name} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: t.color || "#a855f7" }}
                        />
                        <span className="text-slate-300 font-medium">{t.name}</span>
                        {t.badgeText && (
                          <span className="text-[10px] bg-slate-800 text-purple-300 px-1.5 py-0.5 rounded border border-purple-500/20">
                            {t.badgeText}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2.5 w-44">
                        <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                              width: `${Math.max(t.subscribersPercentage, 2)}%`,
                              backgroundColor: t.color || "#a855f7",
                            }}
                          />
                        </div>
                        <span className="text-slate-400 font-mono w-16 text-right">
                          {t.subscribers} ({t.subscribersPercentage}%)
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="py-12 text-center text-slate-500 text-sm">
                No active subscription tier data available.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tables Row: Recent Activity & Top Performing Videos */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Activity Feed */}
        <Card className="bg-slate-900/60 backdrop-blur-xl border-slate-800/80 shadow-xl">
          <CardHeader className="border-b border-slate-800/60 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <CardTitle className="text-lg font-semibold text-white flex items-center gap-2">
                  Recent Activity & Signups
                </CardTitle>
                <div className="text-xs text-slate-400 mt-0.5">Live member telemetry from mobile app users</div>
              </div>
              <div className="flex items-center bg-slate-800/80 p-0.5 rounded-lg border border-slate-700/60">
                {RECENT_FILTERS.map((f) => (
                  <button
                    key={f.value}
                    onClick={() => handleFilterChange(f.value)}
                    className={`px-2.5 py-1 text-xs rounded-md transition-all ${
                      recentFilter === f.value
                        ? "bg-purple-600 text-white font-medium shadow-sm"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            {activityLoading ? (
              <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-purple-400" /> Loading recent activity...
              </div>
            ) : !Array.isArray(recentActivity) || recentActivity.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                No member records found for this filter.
              </div>
            ) : (
              <div className="space-y-3.5">
                {recentActivity.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/40 border border-transparent hover:border-slate-800 transition-all"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      {user.avatarUrl ? (
                        <img
                          src={user.avatarUrl}
                          alt={user.name || "User"}
                          className="h-10 w-10 rounded-full object-cover border border-purple-500/20 flex-shrink-0"
                        />
                      ) : (
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-md flex-shrink-0">
                          {(user.name || user.email || "U").charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="font-semibold text-sm text-slate-100 truncate">
                          {user.name || (user.email ? user.email.split("@")[0] : `User #${user.id}`)}
                        </div>
                        <div className="text-xs text-slate-400 font-mono truncate">
                          {user.email || "Registered via App"}
                        </div>
                      </div>
                    </div>
                    <div className="text-right flex-shrink-0 pl-3">
                      <div className="flex items-center gap-1.5 justify-end">
                        <span className="inline-block text-xs font-semibold px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20">
                          {user.planName || (user.isPaid ? "Paid Member" : "Free Plan")}
                        </span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase ${
                            user.isPaid
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                          }`}
                        >
                          {user.isPaid ? "Subscriber" : "Signup"}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                        {formatDate(user.subscribedAt || user.joinedAt)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Performing Content */}
        <Card className="bg-slate-900/60 backdrop-blur-xl border-slate-800/80 shadow-xl">
          <CardHeader className="border-b border-slate-800/60 pb-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg font-semibold text-white">Top Performing Content</CardTitle>
                <div className="text-xs text-slate-400 mt-0.5">Top viewed streams & video titles</div>
              </div>
              <span className="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-md font-mono">
                Catalog Rank
              </span>
            </div>
          </CardHeader>
          <CardContent className="pt-4">
            {loading && topVideos.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-purple-400" /> Loading video rankings...
              </div>
            ) : topVideos.length === 0 ? (
              <div className="py-12 text-center text-slate-500 text-sm">
                No published video content found.
              </div>
            ) : (
              <div className="space-y-3.5">
                {topVideos.map((video) => (
                  <div
                    key={video.id}
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/40 border border-transparent hover:border-slate-800 transition-all"
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {video.thumbnailUrl || video.mainThumbnailUrl ? (
                        <img
                          src={video.thumbnailUrl || video.mainThumbnailUrl}
                          alt={video.title}
                          className="h-11 w-16 rounded-lg object-cover border border-purple-500/20 flex-shrink-0"
                        />
                      ) : (
                        <div className="h-11 w-16 rounded-lg bg-gradient-to-br from-purple-900/80 to-slate-900 border border-purple-500/20 flex items-center justify-center flex-shrink-0">
                          <PlaySquare className="h-5 w-5 text-purple-400" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm text-slate-200 truncate">{video.title}</div>
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
                          {video.category && (
                            <span className="text-purple-400">{video.category}</span>
                          )}
                          {video.duration && (
                            <span className="flex items-center gap-1 text-slate-500">
                              <Clock className="h-3 w-3" /> {video.duration}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="text-right pl-3 flex-shrink-0">
                      <div className="font-bold text-sm text-purple-300 font-mono">
                        {typeof video.views === "number"
                          ? video.views.toLocaleString()
                          : video.views || "0"}
                      </div>
                      <div className="text-[10px] text-slate-500 uppercase tracking-wider">views</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}



