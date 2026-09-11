import { useState, useEffect, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Button } from "../components/ui/button";
import { Download, TrendingUp, TrendingDown, Eye, Users, PlayCircle, Loader2, CreditCard, Video, RefreshCw } from "lucide-react";
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
  getVideos,
  ApiDashboardStats,
  ApiAnalytics,
  ApiSubscriptionBreakdown,
  ApiVideo,
} from "../services/apiService";

export default function Analytics() {
  const [selectedRange, setSelectedRange] = useState<string>("30");
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<ApiDashboardStats | null>(null);
  const [analytics, setAnalytics] = useState<ApiAnalytics | null>(null);
  const [breakdown, setBreakdown] = useState<ApiSubscriptionBreakdown | null>(null);
  const [videos, setVideos] = useState<ApiVideo[]>([]);

  // Map selected range days to API range parameter
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

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, analyticsRes, breakdownRes, videosRes] = await Promise.all([
        getDashboardStats({ range: apiRange }).catch(() => null),
        getDashboardAnalytics({ range: apiRange, interval: selectedRange === "7" || selectedRange === "30" ? "day" : "month" }).catch(() => null),
        getDashboardSubscriptionBreakdown({ range: apiRange }).catch(() => null),
        getVideos({ status: "published", sort: "views", limit: 50 }).catch(() => ({ data: [] })),
      ]);

      setStats(statsRes);
      setAnalytics(analyticsRes);
      setBreakdown(breakdownRes);
      setVideos(videosRes.data || []);
    } catch (err) {
      console.warn("Error fetching analytics data", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [apiRange]);

  // Aggregate views and video counts per category from real video catalog
  const categoryData = useMemo(() => {
    const catMap: Record<string, { views: number; count: number }> = {};
    videos.forEach((v) => {
      const cat = v.category || "General";
      if (!catMap[cat]) catMap[cat] = { views: 0, count: 0 };
      const vViews = typeof v.views === "number" ? v.views : parseInt(String(v.views || 0), 10) || 0;
      catMap[cat].views += vViews;
      catMap[cat].count += 1;
    });

    return Object.keys(catMap).map((cat) => ({
      category: cat,
      views: catMap[cat].views,
      videos: catMap[cat].count,
    }));
  }, [videos]);

  // Top performing videos for reach distribution
  const topVideos = useMemo(() => {
    return [...videos]
      .sort((a, b) => {
        const va = typeof a.views === "number" ? a.views : parseInt(String(a.views || 0), 10) || 0;
        const vb = typeof b.views === "number" ? b.views : parseInt(String(b.views || 0), 10) || 0;
        return vb - va;
      })
      .slice(0, 5);
  }, [videos]);

  const maxVideoViews = useMemo(() => {
    if (topVideos.length === 0) return 1;
    const topViews = typeof topVideos[0].views === "number" ? topVideos[0].views : parseInt(String(topVideos[0].views || 0), 10) || 0;
    return Math.max(topViews, 1);
  }, [topVideos]);

  // Dynamic KPI metrics computed from live API stats
  const metrics = [
    {
      name: "Total Views",
      value: stats ? stats.totalViews.current.toLocaleString() : "0",
      change: stats
        ? `${stats.totalViews.growth_percentage >= 0 ? "+" : ""}${stats.totalViews.growth_percentage.toFixed(1)}%`
        : "0%",
      trend: stats && stats.totalViews.growth_percentage >= 0 ? "up" : "down",
      icon: Eye,
    },
    {
      name: "Total Users",
      value: stats ? stats.totalUsers.current.toLocaleString() : "0",
      change: stats
        ? `${stats.totalUsers.growth_percentage >= 0 ? "+" : ""}${stats.totalUsers.growth_percentage.toFixed(1)}%`
        : "0%",
      trend: stats && stats.totalUsers.growth_percentage >= 0 ? "up" : "down",
      icon: Users,
    },
    {
      name: "Active Subscribers",
      value: stats ? stats.totalSubscribers.current.toLocaleString() : "0",
      change: stats
        ? `${stats.totalSubscribers.growth_percentage >= 0 ? "+" : ""}${stats.totalSubscribers.growth_percentage.toFixed(1)}%`
        : "0%",
      trend: stats && stats.totalSubscribers.growth_percentage >= 0 ? "up" : "down",
      icon: CreditCard,
    },
    {
      name: "Published Content",
      value: stats ? `${stats.totalContent.published} Videos` : "0 Videos",
      change: stats ? `+${stats.totalContent.recently_added} new` : "0 new",
      trend: "up",
      icon: PlayCircle,
    },
  ];

  const handleExport = () => {
    if (!analytics?.dataPoints || analytics.dataPoints.length === 0) {
      alert("No analytics data available to export.");
      return;
    }
    const headers = ["Date", "Label", "Views", "Active Users", "Subscribers", "Revenue"];
    const rows = analytics.dataPoints.map((p) => [
      p.date,
      p.label,
      p.views,
      p.users,
      p.subscribers,
      p.revenue,
    ]);
    const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `analytics_${apiRange}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
          <p className="text-slate-300 mt-1 font-medium">Track your live content performance and audience insights</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={selectedRange} onValueChange={(val) => setSelectedRange(val)}>
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
            Export
          </Button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <Card key={metric.name} className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-2">
                <metric.icon className="h-5 w-5 text-purple-400" />
                <div
                  className={`flex items-center gap-1 text-sm font-semibold ${
                    metric.trend === "up" ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {metric.trend === "up" ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                  {metric.change}
                </div>
              </div>
              <div className="text-2xl font-bold text-white">
                {loading && !stats ? (
                  <span className="inline-block w-16 h-7 bg-slate-800 animate-pulse rounded" />
                ) : (
                  metric.value
                )}
              </div>
              <div className="text-sm text-slate-300 font-medium">{metric.name}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Views & Audience Activity Chart */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <CardHeader className="border-b border-slate-800 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-white">Views & Active Audience Trends</CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">Timeline performance for selected period</p>
          </div>
          {loading && <Loader2 className="h-4 w-4 animate-spin text-purple-400" />}
        </CardHeader>
        <CardContent className="pt-6">
          {analytics?.dataPoints && analytics.dataPoints.length > 0 ? (
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={analytics.dataPoints}>
                <defs>
                  <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="label" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    borderColor: "#334155",
                    borderRadius: "12px",
                    color: "#f8fafc",
                  }}
                />
                <Legend wrapperStyle={{ color: "#cbd5e1" }} />
                <Area
                  key="views"
                  type="monotone"
                  dataKey="views"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorViews)"
                  name="Views"
                />
                <Area
                  key="users"
                  type="monotone"
                  dataKey="users"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorUsers)"
                  name="Active Users"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[350px] flex flex-col items-center justify-center text-slate-500">
              {loading ? (
                <Loader2 className="h-8 w-8 animate-spin text-purple-500 mb-2" />
              ) : (
                <>
                  <Eye className="h-10 w-10 mb-2 stroke-[1.5]" />
                  <p className="text-sm">No activity recorded for this period yet.</p>
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Engagement by Category */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-slate-800">
            <CardTitle className="text-white">Content Views by Category</CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">Aggregated audience reach across categories</p>
          </CardHeader>
          <CardContent className="pt-6">
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="category" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "12px",
                      color: "#f8fafc",
                    }}
                  />
                  <Legend wrapperStyle={{ color: "#cbd5e1" }} />
                  <Bar key="views" dataKey="views" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Total Views" />
                  <Bar key="videos" dataKey="videos" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Videos" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex flex-col items-center justify-center text-slate-500">
                <Video className="h-10 w-10 mb-2 stroke-[1.5]" />
                <p className="text-sm">No category distribution data available.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Subscription Tier Distribution */}
        <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
          <CardHeader className="border-b border-slate-800">
            <CardTitle className="text-white">Subscription Tier Distribution</CardTitle>
            <p className="text-xs text-slate-400 mt-0.5">Subscriber share across membership tiers</p>
          </CardHeader>
          <CardContent className="pt-6">
            {breakdown?.tiers && breakdown.tiers.length > 0 ? (
              <div className="space-y-4">
                {breakdown.tiers.map((tier) => (
                  <div key={tier.planId}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-200">{tier.name}</span>
                        {tier.badgeText && (
                          <span className="text-[10px] bg-purple-950/80 text-purple-300 border border-purple-800/60 px-1.5 py-0.5 rounded-full font-medium">
                            {tier.badgeText}
                          </span>
                        )}
                      </div>
                      <span className="text-sm text-slate-300 font-medium">
                        {tier.subscribers.toLocaleString()} subscribers ({tier.subscribersPercentage.toFixed(1)}%)
                      </span>
                    </div>
                    <div className="h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(Math.max(tier.subscribersPercentage, 0), 100)}%`,
                          backgroundColor: tier.color || "#8b5cf6",
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-[180px] flex flex-col items-center justify-center text-slate-500">
                <CreditCard className="h-8 w-8 mb-2 stroke-[1.5]" />
                <p className="text-sm">No subscription tiers data recorded.</p>
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-slate-800">
              <div className="text-sm font-semibold text-white mb-3">Audience Insights</div>
              <div className="space-y-2 text-sm text-slate-300 font-medium">
                <p>
                  • Paid subscriber conversion rate:{" "}
                  <span className="text-purple-300 font-semibold">
                    {stats && stats.totalUsers.current > 0
                      ? `${((stats.totalSubscribers.current / stats.totalUsers.current) * 100).toFixed(1)}%`
                      : "0.0%"}
                  </span>
                </p>
                <p>
                  • Total active subscribers:{" "}
                  <span className="text-purple-300 font-semibold">
                    {breakdown?.totalSubscribers.toLocaleString() || "0"}
                  </span>
                </p>
                <p>
                  • Published library reach:{" "}
                  <span className="text-purple-300 font-semibold">
                    {stats?.totalContent.published || 0} active videos
                  </span>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Top Performing Content Distribution */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <CardHeader className="border-b border-slate-800">
          <CardTitle className="text-white">Top Performing Content</CardTitle>
          <p className="text-xs text-slate-400 mt-0.5">Highest audience reach across published videos</p>
        </CardHeader>
        <CardContent className="pt-6">
          {topVideos.length > 0 ? (
            <div className="space-y-4">
              {topVideos.map((video) => {
                const vViews = typeof video.views === "number" ? video.views : parseInt(String(video.views || 0), 10) || 0;
                const pct = Math.round((vViews / maxVideoViews) * 100);
                return (
                  <div
                    key={video.id}
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800/80 pb-4 last:border-0 last:pb-0 gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="h-10 w-14 rounded-md overflow-hidden bg-slate-800 shrink-0 border border-slate-700/60">
                        {video.thumbnailUrl || video.mainThumbnailUrl ? (
                          <img
                            src={video.thumbnailUrl || video.mainThumbnailUrl}
                            alt={video.title}
                            className="h-full w-full object-cover"
                          />
                        ) : (
                          <div className="h-full w-full flex items-center justify-center text-slate-500">
                            <Video className="h-4 w-4" />
                          </div>
                        )}
                      </div>
                      <div className="min-w-0">
                        <div className="font-semibold text-slate-200 truncate">{video.title}</div>
                        <div className="text-xs text-purple-400 font-medium">{video.category || "General"}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6 self-end sm:self-center">
                      <div className="text-right">
                        <div className="font-bold text-white">{vViews.toLocaleString()}</div>
                        <div className="text-xs text-slate-400 font-medium">views</div>
                      </div>
                      <div className="w-32 h-2.5 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                        <div
                          className="h-full bg-gradient-to-r from-purple-600 to-blue-600 rounded-full"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="py-8 flex flex-col items-center justify-center text-slate-500">
              <Video className="h-10 w-10 mb-2 stroke-[1.5]" />
              <p className="text-sm">No published videos found.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
