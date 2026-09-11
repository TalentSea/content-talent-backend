import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import { Label } from "../components/ui/label";
import {
  MessageSquare, Megaphone, Plus, Send, ThumbsUp, Trash2,
  SlidersHorizontal, Search, X, Calendar, ChevronLeft, ChevronRight,
  CornerDownRight, Edit, Loader2, Heart, MessageCircle,
} from "lucide-react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  getAdminComments, getCommentReplies, postCommentReply, toggleCommentLike, deleteComment,
  getCategories, getVideos, ApiComment, ApiReply, ApiCategory, ApiVideo,
} from "../services/apiService";

// ── Types ──────────────────────────────────────────────────────────────────

type Announcement = { id: number; title: string; content: string; date: string; views: number };

type Announcement = { id: number; title: string; content: string; date: string; views: number };

const PAGE_SIZE = 5;

// ── Date picker dialog ─────────────────────────────────────────────────────
function DatePickerDialog({ open, onClose, value, onChange }: {
  open: boolean; onClose: () => void; value: string; onChange: (v: string) => void;
}) {
  const [local, setLocal] = useState(value);
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-xs">
        <DialogHeader>
          <DialogTitle>Filter by Date</DialogTitle>
          <DialogDescription>Show comments posted on a specific date</DialogDescription>
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

// ── Video picker dialog ────────────────────────────────────────────────────
function VideoPickerDialog({ open, onClose, category, onSelect }: {
  open: boolean; onClose: () => void; category: string; onSelect: (v: { id: number; title: string }) => void;
}) {
  const [videoSearch, setVideoSearch] = useState("");
  const [liveVideos, setLiveVideos] = useState<Array<{ id: number; title: string }>>([]);
  const [loadingVideos, setLoadingVideos] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoadingVideos(true);
    getVideos({ category: category || undefined, limit: 100 })
      .then((res) => {
        if (res.data && res.data.length > 0) {
          setLiveVideos(res.data.map((v) => ({ id: v.id, title: v.title })));
        } else {
          setLiveVideos([]);
        }
      })
      .catch(() => {
        setLiveVideos([]);
      })
      .finally(() => setLoadingVideos(false));
  }, [open, category]);

  const filtered = liveVideos.filter((v) => v.title.toLowerCase().includes(videoSearch.toLowerCase()));
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Select Video {category ? `— ${category}` : ""}</DialogTitle>
          <DialogDescription>Pick a video to filter comments by</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <Input placeholder="Search videos..." className="pl-9" value={videoSearch} onChange={(e) => setVideoSearch(e.target.value)} />
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {loadingVideos ? (
              <div className="flex items-center justify-center py-6 text-xs text-slate-400 gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-purple-400" /> Loading videos...
              </div>
            ) : filtered.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">No videos found</p>
            ) : (
              filtered.map((v) => (
                <button
                  key={v.id}
                  className="w-full text-left px-3 py-2.5 rounded-md text-sm text-slate-200 hover:bg-purple-950/40 hover:text-purple-300 transition-colors border border-transparent hover:border-purple-800/40 truncate"
                  onClick={() => { onSelect(v); onClose(); setVideoSearch(""); }}
                >
                  {v.title}
                </button>
              ))
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Announcement edit dialog ───────────────────────────────────────────────
function AnnouncementEditDialog({ open, onClose, announcement, onSave }: {
  open: boolean; onClose: () => void; announcement: Announcement | null;
  onSave: (updated: { title: string; content: string }) => void;
}) {
  const [title, setTitle] = useState(announcement?.title ?? "");
  const [content, setContent] = useState(announcement?.content ?? "");

  useEffect(() => {
    if (announcement) {
      setTitle(announcement.title);
      setContent(announcement.content);
    }
  }, [announcement]);

  if (!announcement) return null;
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-slate-900 border border-slate-800 text-slate-100">
        <DialogHeader>
          <DialogTitle className="text-white">Edit Announcement</DialogTitle>
          <DialogDescription className="text-slate-400">Update your announcement details</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label className="text-slate-300">Title</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} className="bg-slate-950 border-slate-800 text-slate-100 mt-1" />
          </div>
          <div>
            <Label className="text-slate-300">Content</Label>
            <Textarea value={content} onChange={(e) => setContent(e.target.value)} rows={5} className="bg-slate-950 border-slate-800 text-slate-100 mt-1" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} className="border-slate-800 bg-slate-800 text-slate-300 hover:bg-slate-700">Cancel</Button>
          <Button
            onClick={() => {
              onSave({ title, content });
              onClose();
            }}
            className="bg-purple-600 hover:bg-purple-500 text-white"
          >
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────
export default function Community() {
  const [announcementOpen, setAnnouncementOpen] = useState(false);
  const [editAnnouncement, setEditAnnouncement] = useState<Announcement | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>(() => {
    try {
      const saved = localStorage.getItem("admin_announcements");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [newAnnouncementTitle, setNewAnnouncementTitle] = useState("");
  const [newAnnouncementContent, setNewAnnouncementContent] = useState("");

  const handleCreateAnnouncement = () => {
    if (!newAnnouncementTitle.trim()) return;
    const newAnn: Announcement = {
      id: Date.now(),
      title: newAnnouncementTitle.trim(),
      content: newAnnouncementContent.trim(),
      date: new Date().toISOString().slice(0, 10),
      views: 0,
    };
    const updated = [newAnn, ...announcements];
    setAnnouncements(updated);
    try {
      localStorage.setItem("admin_announcements", JSON.stringify(updated));
    } catch {}
    setNewAnnouncementTitle("");
    setNewAnnouncementContent("");
    setAnnouncementOpen(false);
  };

  const handleSaveEditAnnouncement = (updatedData: { title: string; content: string }) => {
    if (!editAnnouncement) return;
    const updated = announcements.map((a) =>
      a.id === editAnnouncement.id ? { ...a, title: updatedData.title, content: updatedData.content } : a
    );
    setAnnouncements(updated);
    try {
      localStorage.setItem("admin_announcements", JSON.stringify(updated));
    } catch {}
    setEditAnnouncement(null);
  };

  const handleDeleteAnnouncement = (id: number) => {
    const updated = announcements.filter((a) => a.id !== id);
    setAnnouncements(updated);
    try {
      localStorage.setItem("admin_announcements", JSON.stringify(updated));
    } catch {}
  };

  // Filters
  const [showFilters, setShowFilters] = useState(false);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterVideoId, setFilterVideoId] = useState<number | null>(null);
  const [filterVideoTitle, setFilterVideoTitle] = useState("");
  const [filterDate, setFilterDate] = useState("");
  const [filterMinLikes, setFilterMinLikes] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [page, setPage] = useState(1);

  // Live Comments State
  const [comments, setComments] = useState<ApiComment[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [dynamicCategories, setDynamicCategories] = useState<string[]>([]);

  useEffect(() => {
    getCategories({ simple: true })
      .then((cats) => {
        if (cats && cats.length > 0) {
          setDynamicCategories(cats.map((c) => c.name));
        }
      })
      .catch((err) => console.warn("Failed to fetch category list for community filters", err));
  }, []);

  // Dialog & Thread states
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [videoPickerOpen, setVideoPickerOpen] = useState(false);
  const [replyOpenId, setReplyOpenId] = useState<number | string | null>(null);
  const [replyText, setReplyText] = useState("");
  const [submittingReply, setSubmittingReply] = useState(false);
  
  // Thread replies cache: commentId -> ApiReply[]
  const [openRepliesId, setOpenRepliesId] = useState<number | null>(null);
  const [repliesCache, setRepliesCache] = useState<Record<number, ApiReply[]>>({});
  const [loadingReplies, setLoadingReplies] = useState(false);

  // Fetch comments from API
  const fetchComments = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getAdminComments({
        category: filterCategory !== "all" ? filterCategory : undefined,
        videoId: filterVideoId || undefined,
        date: filterDate || undefined,
        minLikes: filterMinLikes ? parseInt(filterMinLikes) : undefined,
        search: search || undefined,
        sort: sortBy,
        page,
        limit: PAGE_SIZE,
      });
      setComments(res.data);
      setTotalCount(res.pagination?.total || res.data.length);
    } catch (err) {
      console.warn("Failed to load comments from API", err);
      setComments([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [filterCategory, filterVideoId, filterDate, filterMinLikes, search, sortBy, page]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const activeFilterCount =
    (filterCategory !== "all" ? 1 : 0) +
    (filterVideoId !== null ? 1 : 0) +
    (filterDate ? 1 : 0) +
    (filterMinLikes ? 1 : 0);

  const resetFilters = () => {
    setFilterCategory("all"); setFilterVideoId(null); setFilterVideoTitle(""); setFilterDate("");
    setFilterMinLikes(""); setSortBy("newest"); setSearch(""); setPage(1);
  };

  const handleCategoryChange = (v: string) => {
    setFilterCategory(v);
    setFilterVideoId(null);
    setFilterVideoTitle("");
    setPage(1);
  };

  // Toggle Like API Call
  const handleToggleLike = async (commentId: number) => {
    try {
      const res = await toggleCommentLike(commentId);
      setComments((prev) =>
        prev.map((c) =>
          c.id === commentId ? { ...c, isLiked: res.isLiked, likes: res.likes } : c
        )
      );
    } catch (err) {
      console.error("Failed to toggle like", err);
      // Optimistic fallback
      setComments((prev) =>
        prev.map((c) =>
          c.id === commentId ? { ...c, isLiked: !c.isLiked, likes: c.isLiked ? c.likes - 1 : c.likes + 1 } : c
        )
      );
    }
  };

  // Delete Comment API Call
  const handleDeleteComment = async (commentId: number) => {
    if (!confirm("Are you sure you want to delete this comment?")) return;
    try {
      await deleteComment(commentId);
      fetchComments();
    } catch (err) {
      console.error("Failed to delete comment", err);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
    }
  };

  // Toggle replies thread view
  const handleToggleReplies = async (commentId: number) => {
    if (openRepliesId === commentId) {
      setOpenRepliesId(null);
      return;
    }
    setOpenRepliesId(commentId);
    if (!repliesCache[commentId]) {
      setLoadingReplies(true);
      try {
        const res = await getCommentReplies(commentId);
        setRepliesCache((prev) => ({ ...prev, [commentId]: res.data }));
      } catch (err) {
        console.warn("Failed to load replies", err);
      } finally {
        setLoadingReplies(false);
      }
    }
  };

  const handleToggleReplyLike = async (parentCommentId: number, replyId: number) => {
    try {
      const res = await toggleCommentLike(replyId);
      setRepliesCache((prev) => ({
        ...prev,
        [parentCommentId]: (prev[parentCommentId] || []).map((r) =>
          r.id === replyId ? { ...r, isLiked: res.isLiked, likes: res.likes } : r
        ),
      }));
    } catch (err) {
      console.error("Failed to toggle reply like", err);
    }
  };

  // Post Creator Reply (supports top-level comment or sub-comment target)
  const handleSendReply = async (parentCommentId: number, targetReplyId?: number) => {
    if (!replyText.trim()) return;
    setSubmittingReply(true);
    try {
      const targetId = targetReplyId ?? parentCommentId;
      const newReply = await postCommentReply(targetId, replyText);
      setRepliesCache((prev) => ({
        ...prev,
        [parentCommentId]: [...(prev[parentCommentId] || []), newReply],
      }));
      setComments((prev) =>
        prev.map((c) => (c.id === parentCommentId ? { ...c, replyCount: c.replyCount + 1 } : c))
      );
      setOpenRepliesId(parentCommentId);
      setReplyText("");
      setReplyOpenId(null);
    } catch (err) {
      console.error("Failed to post reply", err);
    } finally {
      setSubmittingReply(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  return (
    <div className="space-y-6">
      {/* Controlled dialogs */}
      <Dialog open={announcementOpen} onOpenChange={setAnnouncementOpen}>
        <DialogContent className="max-w-2xl bg-slate-900 border border-slate-800 text-slate-100">
          <DialogHeader>
            <DialogTitle className="text-white">Create Announcement</DialogTitle>
            <DialogDescription className="text-slate-400">Share important updates with your subscribers</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-slate-300">Title</Label>
              <Input
                placeholder="Enter announcement title"
                value={newAnnouncementTitle}
                onChange={(e) => setNewAnnouncementTitle(e.target.value)}
                className="bg-slate-950 border-slate-800 text-slate-100 mt-1"
              />
            </div>
            <div>
              <Label className="text-slate-300">Content</Label>
              <Textarea
                placeholder="Write your announcement here..."
                rows={6}
                value={newAnnouncementContent}
                onChange={(e) => setNewAnnouncementContent(e.target.value)}
                className="bg-slate-950 border-slate-800 text-slate-100 mt-1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAnnouncementOpen(false)} className="border-slate-800 bg-slate-800 text-slate-300 hover:bg-slate-700">Cancel</Button>
            <Button className="gap-2 bg-purple-600 hover:bg-purple-500 text-white" onClick={handleCreateAnnouncement}><Send className="h-4 w-4" />Publish</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AnnouncementEditDialog
        open={!!editAnnouncement}
        onClose={() => setEditAnnouncement(null)}
        announcement={editAnnouncement}
        onSave={handleSaveEditAnnouncement}
      />

      <DatePickerDialog
        open={datePickerOpen}
        onClose={() => setDatePickerOpen(false)}
        value={filterDate}
        onChange={(v) => { setFilterDate(v); setPage(1); }}
      />

      <VideoPickerDialog
        open={videoPickerOpen}
        onClose={() => setVideoPickerOpen(false)}
        category={filterCategory === "all" ? "" : filterCategory}
        onSelect={(v) => { setFilterVideoId(v.id); setFilterVideoTitle(v.title); setPage(1); }}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Community</h1>
          <p className="text-slate-300 mt-1 font-medium">Engage with your audience and manage discussions</p>
        </div>
        <Button className="gap-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold shadow-lg shadow-purple-600/20" onClick={() => setAnnouncementOpen(true)}>
          <Plus className="h-4 w-4" />New Announcement
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        {[
          { name: "Total Comments", value: totalCount.toLocaleString(), icon: MessageSquare, color: "text-blue-400", bgColor: "bg-blue-500/10 border border-blue-500/20" },
          { name: "Announcements", value: announcements.length.toString(), icon: Megaphone, color: "text-purple-400", bgColor: "bg-purple-500/10 border border-purple-500/20" },
          { name: "Active Discussions", value: comments.length > 0 ? `${new Set(comments.map((c) => c.videoId)).size} videos` : "0 videos", icon: ThumbsUp, color: "text-emerald-400", bgColor: "bg-emerald-500/10 border border-emerald-500/20" },
        ].map((stat) => (
          <Card key={stat.name} className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className={`${stat.bgColor} ${stat.color} p-3 rounded-lg`}>
                  <stat.icon className="h-6 w-6" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-sm text-slate-300 font-medium">{stat.name}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Announcements */}
      <Card className="border-slate-800 bg-slate-900/60 backdrop-blur-sm">
        <CardHeader className="border-b border-slate-800"><CardTitle className="text-white">Recent Announcements</CardTitle></CardHeader>
        <CardContent className="p-6">
          {announcements.length > 0 ? (
            <div className="space-y-4">
              {announcements.map((a) => (
                <div key={a.id} className="border border-slate-800 rounded-xl p-4 hover:border-purple-500/50 transition-colors bg-slate-950/40">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-lg text-slate-100">{a.title}</h3>
                    <Button variant="ghost" size="icon" onClick={() => handleDeleteAnnouncement(a.id)}>
                      <Trash2 className="h-4 w-4 text-rose-400 hover:text-rose-300" />
                    </Button>
                  </div>
                  <p className="text-slate-300 mb-3 font-medium leading-relaxed">{a.content}</p>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4">
                      <span className="text-slate-400 font-medium">{a.date}</span>
                      <span className="text-slate-400 font-medium">{a.views.toLocaleString()} views</span>
                    </div>
                    <Button variant="outline" size="sm" className="gap-1.5 border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700" onClick={() => setEditAnnouncement(a)}>
                      <Edit className="h-3.5 w-3.5 text-purple-400" />Edit
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 flex flex-col items-center justify-center text-slate-500">
              <Megaphone className="h-8 w-8 mb-2 stroke-[1.5]" />
              <p className="text-sm">No announcements published yet.</p>
              <p className="text-xs text-slate-400 mt-0.5">Click "New Announcement" above to broadcast an update to your community.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Comments with filters + pagination */}
      <Card className="border-slate-800">
        <CardHeader className="border-b border-slate-800">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CardTitle className="text-white">Comments</CardTitle>
                <span className="text-sm text-slate-400 font-medium">{totalCount} total</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                  <Input placeholder="Search comments..." className="pl-9 w-56 bg-slate-950/80 border-slate-800 text-slate-100 placeholder:text-slate-500"
                    value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
                </div>
                <Button variant={showFilters ? "default" : "outline"} className={`gap-2 border-slate-800 ${showFilters ? "bg-purple-600 text-white hover:bg-purple-500" : "bg-slate-900 text-slate-300 hover:bg-slate-800"}`}
                  onClick={() => setShowFilters(!showFilters)}>
                  <SlidersHorizontal className="h-4 w-4" />
                  Filters
                  {activeFilterCount > 0 && (
                    <span className="ml-1 bg-white/20 text-white rounded-full text-xs font-bold px-1.5">{activeFilterCount}</span>
                  )}
                </Button>
              </div>
            </div>

            {showFilters && (
              <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <Label className="text-xs mb-1 block text-slate-400 font-semibold uppercase tracking-wider">Category</Label>
                    <Select value={filterCategory} onValueChange={handleCategoryChange}>
                      <SelectTrigger className="h-9 text-sm bg-slate-900 border-slate-800 text-slate-100"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                        <SelectItem value="all">All Categories</SelectItem>
                        {dynamicCategories.map((c) => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-xs mb-1 block text-slate-400 font-semibold uppercase tracking-wider">Video</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-9 text-sm w-full justify-start gap-1.5 bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
                      onClick={() => setVideoPickerOpen(true)}
                    >
                      <span className="truncate flex-1 text-left">
                        {filterVideoTitle || "All Videos"}
                      </span>
                      {filterVideoId !== null && (
                        <span
                          role="button"
                          tabIndex={0}
                          aria-label="Clear video filter"
                          className="ml-auto p-0.5 rounded hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
                          onClick={(e) => {
                            e.stopPropagation();
                            setFilterVideoId(null);
                            setFilterVideoTitle("");
                            setPage(1);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.stopPropagation();
                              setFilterVideoId(null);
                              setFilterVideoTitle("");
                              setPage(1);
                            }
                          }}
                        >
                          <X className="h-3.5 w-3.5" />
                        </span>
                      )}
                    </Button>
                  </div>

                  <div>
                    <Label className="text-xs mb-1 block text-slate-400 font-semibold uppercase tracking-wider">Date</Label>
                    <Button variant="outline" size="sm" className="h-9 gap-1.5 text-sm w-full justify-start bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
                      onClick={() => setDatePickerOpen(true)}>
                      <Calendar className="h-3.5 w-3.5 flex-shrink-0 text-slate-400" />
                      <span className="truncate flex-1 text-left">{filterDate || "Pick date"}</span>
                    </Button>
                  </div>

                  <div>
                    <Label className="text-xs mb-1 block text-slate-400 font-semibold uppercase tracking-wider">Min Likes</Label>
                    <Input
                      type="number"
                      min={0}
                      placeholder="e.g. 10"
                      className="h-9 text-sm bg-slate-900 border-slate-800 text-slate-100 placeholder:text-slate-500"
                      value={filterMinLikes}
                      onChange={(e) => { setFilterMinLikes(e.target.value); setPage(1); }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Sort by:</Label>
                    <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setPage(1); }}>
                      <SelectTrigger className="h-8 text-sm w-36 bg-slate-900 border-slate-800 text-slate-100"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                        <SelectItem value="newest">Newest first</SelectItem>
                        <SelectItem value="oldest">Oldest first</SelectItem>
                        <SelectItem value="mostLiked">Most liked</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {activeFilterCount > 0 && (
                    <Button variant="ghost" size="sm" className="gap-1 text-xs text-purple-400 hover:text-purple-300 h-8" onClick={resetFilters}>
                      <X className="h-3 w-3" />Clear filters
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
              <Loader2 className="h-5 w-5 animate-spin" /> Loading comments...
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <MessageSquare className="h-10 w-10 mx-auto mb-3 opacity-40" />
              <p className="font-medium">No comments found</p>
              <Button variant="link" className="text-purple-600 mt-1" onClick={resetFilters}>Clear all filters</Button>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                {comments.map((comment) => (
                  <div key={comment.id} className="border border-gray-200 dark:border-slate-800 rounded-xl p-4 transition-all">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white font-semibold flex-shrink-0 overflow-hidden">
                          {comment.userAvatar ? (
                            <img src={comment.userAvatar} alt={comment.userName} className="w-full h-full object-cover" />
                          ) : (
                            comment.userName.charAt(0)
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-sm text-slate-900 dark:text-white">{comment.userName}</div>
                          <div className="text-xs text-slate-500">
                            on <span className="font-medium text-slate-700 dark:text-slate-300">{comment.videoTitle || `Video #${comment.videoId}`}</span> · {new Date(comment.createdAt).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteComment(comment.id)}
                        className="text-slate-400 hover:text-red-600 h-8 w-8"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>

                    <p className="text-sm text-slate-800 dark:text-slate-200 mb-3 ml-13">{comment.text}</p>

                    <div className="flex items-center justify-between ml-13 text-xs text-slate-500">
                      <div className="flex items-center gap-4">
                        <button
                          onClick={() => handleToggleLike(comment.id)}
                          className={`flex items-center gap-1.5 font-medium transition-colors ${comment.isLiked ? "text-purple-600" : "hover:text-purple-600"}`}
                        >
                          <Heart className={`h-4 w-4 ${comment.isLiked ? "fill-purple-600" : ""}`} />
                          {comment.likes}
                        </button>
                        <button
                          onClick={() => handleToggleReplies(comment.id)}
                          className="flex items-center gap-1.5 font-medium hover:text-purple-600 transition-colors"
                        >
                          <MessageCircle className="h-4 w-4" />
                          {comment.replyCount}
                        </button>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1.5 text-xs text-purple-600 hover:text-purple-700"
                        onClick={() => {
                          setReplyOpenId(replyOpenId === comment.id ? null : comment.id);
                          setReplyText("");
                        }}
                      >
                        <CornerDownRight className="h-3.5 w-3.5" /> Reply
                      </Button>
                    </div>

                    {/* Inline reply composer */}
                    {replyOpenId === comment.id && (
                      <div className="mt-3 ml-13 flex gap-2">
                        <Input
                          placeholder={`Reply to ${comment.userName}…`}
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          className="flex-1 h-9 text-xs"
                          autoFocus
                        />
                        <Button
                          size="sm"
                          disabled={!replyText.trim() || submittingReply}
                          onClick={() => handleSendReply(comment.id)}
                          className="bg-slate-900 text-white hover:bg-slate-800"
                        >
                          {submittingReply ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => { setReplyOpenId(null); setReplyText(""); }}>
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}

                    {/* Replies Thread */}
                    {openRepliesId === comment.id && (
                      <div className="mt-3 ml-13 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
                        {loadingReplies ? (
                          <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                            <Loader2 className="h-3.5 w-3.5 animate-spin" /> Loading replies...
                          </div>
                        ) : (repliesCache[comment.id] || []).length === 0 ? (
                          <p className="text-xs text-slate-400 py-1">No replies in this thread yet.</p>
                        ) : (
                          (repliesCache[comment.id] || []).map((reply) => {
                            const isSubReplyOpen = replyOpenId === `reply-${reply.id}`;
                            return (
                              <div key={reply.id} className="bg-slate-50 dark:bg-slate-900/50 p-2.5 rounded-lg text-xs space-y-1.5 border border-slate-200/50 dark:border-slate-800/60">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
                                      {reply.userName}
                                      {reply.isCreator && (
                                        <Badge className="bg-purple-950/80 border-purple-800 text-purple-300 text-[10px] px-1.5 py-0">
                                          Creator
                                        </Badge>
                                      )}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <span className="text-[10px] text-slate-400">{new Date(reply.createdAt).toLocaleDateString()}</span>
                                  </div>
                                </div>
                                <p className="text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-line">{reply.text}</p>

                                {/* Subcomment stats and reply button bar */}
                                <div className="flex items-center justify-between pt-1 text-xs text-slate-500">
                                  <div className="flex items-center gap-4">
                                    <button
                                      type="button"
                                      onClick={() => handleToggleReplyLike(comment.id, reply.id)}
                                      className={`flex items-center gap-1.5 font-medium transition-colors cursor-pointer ${reply.isLiked ? "text-purple-600 dark:text-purple-400" : "hover:text-purple-600 dark:hover:text-purple-400"}`}
                                    >
                                      <Heart className={`h-3.5 w-3.5 ${reply.isLiked ? "fill-purple-600 text-purple-600 dark:fill-purple-400 dark:text-purple-400" : ""}`} />
                                      {reply.likes || 0}
                                    </button>
                                  </div>

                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 px-2 text-xs text-purple-600 hover:text-purple-700 gap-1 cursor-pointer"
                                    onClick={() => {
                                      if (isSubReplyOpen) {
                                        setReplyOpenId(null);
                                        setReplyText("");
                                      } else {
                                        setReplyOpenId(`reply-${reply.id}`);
                                        setReplyText(`@${reply.userName} `);
                                      }
                                    }}
                                  >
                                    <CornerDownRight className="h-3.5 w-3.5" /> Reply
                                  </Button>
                                </div>

                                {/* Inline sub-comment reply composer */}
                                {isSubReplyOpen && (
                                  <div className="mt-2 flex gap-2">
                                    <Input
                                      placeholder={`Reply to ${reply.userName}...`}
                                      value={replyText}
                                      onChange={(e) => setReplyText(e.target.value)}
                                      className="flex-1 h-8 text-xs bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-700"
                                      autoFocus
                                    />
                                    <Button
                                      size="sm"
                                      disabled={!replyText.trim() || submittingReply}
                                      onClick={() => handleSendReply(comment.id, reply.id)}
                                      className="bg-purple-600 text-white hover:bg-purple-700 h-8 px-3 text-xs cursor-pointer"
                                    >
                                      {submittingReply ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-8 w-8 p-0 text-slate-400 cursor-pointer"
                                      onClick={() => { setReplyOpenId(null); setReplyText(""); }}
                                    >
                                      <X className="h-3.5 w-3.5" />
                                    </Button>
                                  </div>
                                )}
                              </div>
                            );
                          })
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-4 border-t">
                  <p className="text-sm text-gray-500">
                    Page {page} of {totalPages}
                  </p>
                  <div className="flex items-center gap-1">
                    <Button variant="outline" size="icon" className="h-8 w-8"
                      disabled={page === 1} onClick={() => setPage(page - 1)}>
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="icon" className="h-8 w-8"
                      disabled={page === totalPages} onClick={() => setPage(page + 1)}>
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
