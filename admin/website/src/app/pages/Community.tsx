import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
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


const PAGE_SIZE = 5;

// ── Date picker dialog ─────────────────────────────────────────────────────
function DatePickerDialog({ open, onClose, value, onChange }: {
  open: boolean; onClose: () => void; value: string; onChange: (v: string) => void;
}) {
  const [local, setLocal] = useState(value);
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-xs bg-white border border-slate-200/80 text-slate-900 rounded-2xl shadow-xl">
        <DialogHeader>
          <DialogTitle className="text-base font-bold text-slate-900">Filter by Date</DialogTitle>
          <DialogDescription className="text-xs text-slate-500">Show comments posted on a specific date</DialogDescription>
        </DialogHeader>
        <div className="py-2">
          <Input type="date" value={local} onChange={(e) => setLocal(e.target.value)} className="rounded-xl border-slate-200 text-sm" />
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={() => { onChange(""); setLocal(""); onClose(); }} className="rounded-xl border-slate-200 text-xs font-semibold hover:bg-slate-50">Clear</Button>
          <Button onClick={() => { onChange(local); onClose(); }} className="bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-xs">Apply</Button>
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
      <DialogContent className="max-w-sm bg-white border border-slate-200/80 text-slate-900 rounded-2xl shadow-xl">
        <DialogHeader>
          <DialogTitle className="text-base font-bold text-slate-900">Select Video {category ? `— ${category}` : ""}</DialogTitle>
          <DialogDescription className="text-xs text-slate-500">Pick a video to filter comments by</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input placeholder="Search videos..." className="pl-9 rounded-xl border-slate-200 text-sm" value={videoSearch} onChange={(e) => setVideoSearch(e.target.value)} />
          </div>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {loadingVideos ? (
              <div className="flex items-center justify-center py-6 text-xs text-slate-500 gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-slate-900" /> Loading videos...
              </div>
            ) : filtered.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">No videos found</p>
            ) : (
              filtered.map((v) => (
                <button
                  key={v.id}
                  className="w-full text-left px-3 py-2 rounded-xl text-xs font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors truncate"
                  onClick={() => { onSelect(v); onClose(); setVideoSearch(""); }}
                >
                  {v.title}
                </button>
              ))
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} className="rounded-xl border-slate-200 text-xs font-semibold hover:bg-slate-50">Cancel</Button>
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
      <DialogContent className="max-w-2xl bg-white border border-slate-200/80 text-slate-900 rounded-2xl shadow-xl">
        <DialogHeader>
          <DialogTitle className="text-base font-bold text-slate-900">Edit Announcement</DialogTitle>
          <DialogDescription className="text-xs text-slate-500">Update your announcement details</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label className="text-xs font-semibold text-slate-700">Title</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} className="rounded-xl border-slate-200 text-sm mt-1" />
          </div>
          <div>
            <Label className="text-xs font-semibold text-slate-700">Content</Label>
            <Textarea value={content} onChange={(e) => setContent(e.target.value)} rows={5} className="rounded-xl border-slate-200 text-sm mt-1 resize-none" />
          </div>
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose} className="rounded-xl border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold">Cancel</Button>
          <Button
            onClick={() => {
              onSave({ title, content });
              onClose();
            }}
            className="bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-xs"
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
    toast.success("Announcement published successfully.");
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
    toast.success("Announcement updated successfully.");
  };

  const handleDeleteAnnouncement = (id: number) => {
    const updated = announcements.filter((a) => a.id !== id);
    setAnnouncements(updated);
    try {
      localStorage.setItem("admin_announcements", JSON.stringify(updated));
    } catch {}
    toast.success("Announcement deleted successfully.");
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
      toast.success("Comment deleted successfully.");
      fetchComments();
    } catch (err: any) {
      console.error("Failed to delete comment", err);
      toast.error(err?.message || "Something went wrong while deleting comment.");
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
      toast.success("Reply posted successfully.");
    } catch (err: any) {
      console.error("Failed to post reply", err);
      toast.error(err?.message || "Something went wrong while posting reply.");
    } finally {
      setSubmittingReply(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));

  return (
    <div className="space-y-6">
      {/* Controlled dialogs */}
      <Dialog open={announcementOpen} onOpenChange={setAnnouncementOpen}>
        <DialogContent className="max-w-2xl bg-white border border-slate-200/80 text-slate-900 rounded-2xl shadow-xl">
          <DialogHeader>
            <DialogTitle className="text-base font-bold text-slate-900">Create Announcement</DialogTitle>
            <DialogDescription className="text-xs text-slate-500">Share important updates with your channel subscribers</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label className="text-xs font-semibold text-slate-700">Title</Label>
              <Input
                placeholder="Enter announcement title"
                value={newAnnouncementTitle}
                onChange={(e) => setNewAnnouncementTitle(e.target.value)}
                className="rounded-xl border-slate-200 text-sm mt-1"
              />
            </div>
            <div>
              <Label className="text-xs font-semibold text-slate-700">Content</Label>
              <Textarea
                placeholder="Write your announcement here..."
                rows={5}
                value={newAnnouncementContent}
                onChange={(e) => setNewAnnouncementContent(e.target.value)}
                className="rounded-xl border-slate-200 text-sm mt-1 resize-none"
              />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setAnnouncementOpen(false)} className="rounded-xl border-slate-200 text-slate-700 hover:bg-slate-50 text-xs font-semibold">Cancel</Button>
            <Button className="gap-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-xs" onClick={handleCreateAnnouncement}><Send className="h-3.5 w-3.5" />Publish</Button>
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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Community</h1>
          <p className="text-sm text-slate-500 mt-1 font-normal">Engage with your audience and manage channel discussions</p>
        </div>
        <Button className="gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-xl shadow-xs" onClick={() => setAnnouncementOpen(true)}>
          <Plus className="h-4 w-4" />New Announcement
        </Button>
      </div>

      {/* Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        {[
          { name: "Total Comments", value: totalCount.toLocaleString(), icon: MessageSquare },
          { name: "Announcements", value: announcements.length.toString(), icon: Megaphone },
          { name: "Active Discussions", value: comments.length > 0 ? `${new Set(comments.map((c) => c.videoId)).size} videos` : "0 videos", icon: ThumbsUp },
        ].map((stat) => (
          <Card key={stat.name} className="bg-white border border-slate-200/80 shadow-xs rounded-2xl">
            <CardContent className="p-5">
              <div className="flex items-center gap-4">
                <div className="p-2.5 rounded-xl bg-slate-100 text-slate-700">
                  <stat.icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-slate-900 tracking-tight">{stat.value}</div>
                  <div className="text-xs text-slate-500 font-medium mt-0.5">{stat.name}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Announcements */}
      <Card className="bg-white border border-slate-200/80 shadow-xs rounded-2xl">
        <CardHeader className="border-b border-slate-100 pb-4">
          <CardTitle className="text-base font-bold text-slate-900 tracking-tight">Recent Announcements</CardTitle>
        </CardHeader>
        <CardContent className="p-5">
          {announcements.length > 0 ? (
            <div className="space-y-3">
              {announcements.map((a) => (
                <div key={a.id} className="border border-slate-200/80 rounded-xl p-4 hover:border-slate-300 transition-colors bg-slate-50/60">
                  <div className="flex items-start justify-between mb-1.5">
                    <h3 className="font-semibold text-sm text-slate-900">{a.title}</h3>
                    <Button variant="ghost" size="icon" onClick={() => handleDeleteAnnouncement(a.id)} className="h-7 w-7 text-slate-400 hover:text-red-600">
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                  <p className="text-slate-600 text-xs mb-3 leading-relaxed">{a.content}</p>
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-3">
                      <span className="text-slate-400">{a.date}</span>
                      <span className="text-slate-400">{a.views.toLocaleString()} views</span>
                    </div>
                    <Button variant="outline" size="sm" className="gap-1.5 border-slate-200 bg-white text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold shadow-xs" onClick={() => setEditAnnouncement(a)}>
                      <Edit className="h-3 w-3 text-slate-500" />Edit
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 flex flex-col items-center justify-center text-slate-400">
              <Megaphone className="h-8 w-8 mb-2 stroke-[1.5]" />
              <p className="text-sm font-medium text-slate-600">No announcements published yet.</p>
              <p className="text-xs text-slate-400 mt-0.5">Click "New Announcement" above to broadcast an update to your community.</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Comments with filters + pagination */}
      <Card className="bg-white border border-slate-200/80 shadow-xs rounded-2xl">
        <CardHeader className="border-b border-slate-100 pb-4">
          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <CardTitle className="text-base font-bold text-slate-900 tracking-tight">Comments</CardTitle>
                <span className="text-xs text-slate-500 font-medium">{totalCount} total</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
                  <Input
                    placeholder="Search comments..."
                    className="pl-9 w-52 sm:w-60 bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 rounded-xl text-xs h-9"
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  />
                </div>
                <Button
                  variant="outline"
                  className={`gap-2 rounded-xl text-xs font-semibold shadow-xs h-9 ${showFilters ? "bg-slate-900 text-white hover:bg-slate-800 border-slate-900" : "bg-white text-slate-700 hover:bg-slate-50 border-slate-200"}`}
                  onClick={() => setShowFilters(!showFilters)}
                >
                  <SlidersHorizontal className="h-3.5 w-3.5" />
                  Filters
                  {activeFilterCount > 0 && (
                    <span className="ml-1 bg-white/20 text-white rounded-full text-xs font-bold px-1.5">{activeFilterCount}</span>
                  )}
                </Button>
              </div>
            </div>

            {showFilters && (
              <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 space-y-3">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div>
                    <Label className="text-[11px] mb-1 block text-slate-500 font-bold uppercase tracking-wider">Category</Label>
                    <Select value={filterCategory} onValueChange={handleCategoryChange}>
                      <SelectTrigger className="h-9 text-xs bg-white border-slate-200 text-slate-900 rounded-xl"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-white border-slate-200 text-slate-900 rounded-xl">
                        <SelectItem value="all">All Categories</SelectItem>
                        {dynamicCategories.map((c) => (
                          <SelectItem key={c} value={c}>{c}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label className="text-[11px] mb-1 block text-slate-500 font-bold uppercase tracking-wider">Video</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-9 text-xs w-full justify-start gap-1.5 bg-white border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl shadow-xs"
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
                          className="ml-auto p-0.5 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-700 transition-colors"
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
                    <Label className="text-[11px] mb-1 block text-slate-500 font-bold uppercase tracking-wider">Date</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-9 gap-1.5 text-xs w-full justify-start bg-white border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl shadow-xs"
                      onClick={() => setDatePickerOpen(true)}
                    >
                      <Calendar className="h-3.5 w-3.5 flex-shrink-0 text-slate-400" />
                      <span className="truncate flex-1 text-left">{filterDate || "Pick date"}</span>
                    </Button>
                  </div>

                  <div>
                    <Label className="text-[11px] mb-1 block text-slate-500 font-bold uppercase tracking-wider">Min Likes</Label>
                    <Input
                      type="number"
                      min={0}
                      placeholder="e.g. 10"
                      className="h-9 text-xs bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 rounded-xl"
                      value={filterMinLikes}
                      onChange={(e) => { setFilterMinLikes(e.target.value); setPage(1); }}
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-slate-500 font-medium">Sort by:</Label>
                    <Select value={sortBy} onValueChange={(v) => { setSortBy(v); setPage(1); }}>
                      <SelectTrigger className="h-8 text-xs w-36 bg-white border-slate-200 text-slate-900 rounded-xl"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-white border-slate-200 text-slate-900 rounded-xl">
                        <SelectItem value="newest">Newest first</SelectItem>
                        <SelectItem value="oldest">Oldest first</SelectItem>
                        <SelectItem value="mostLiked">Most liked</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {activeFilterCount > 0 && (
                    <Button variant="ghost" size="sm" className="gap-1 text-xs text-slate-600 hover:text-slate-900 h-8 font-medium" onClick={resetFilters}>
                      <X className="h-3 w-3" />Clear filters
                    </Button>
                  )}
                </div>
              </div>
            )}
          </div>
        </CardHeader>

        <CardContent className="p-5">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-slate-400 gap-2">
              <Loader2 className="h-5 w-5 animate-spin text-slate-900" /> Loading comments...
            </div>
          ) : comments.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <MessageSquare className="h-10 w-10 mx-auto mb-3 opacity-30" />
              <p className="font-medium text-slate-700">No comments found</p>
              <Button variant="link" className="text-slate-900 font-semibold mt-1" onClick={resetFilters}>Clear all filters</Button>
            </div>
          ) : (
            <>
              <div className="space-y-3">
                {comments.map((comment) => (
                  <div key={comment.id} className="border border-slate-200/80 rounded-2xl p-4 transition-all bg-white hover:border-slate-300 shadow-xs">
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-full bg-slate-900 flex items-center justify-center text-white font-bold text-xs flex-shrink-0 overflow-hidden shadow-xs">
                          {comment.userAvatar ? (
                            <img src={comment.userAvatar} alt={comment.userName} className="w-full h-full object-cover" />
                          ) : (
                            comment.userName.charAt(0)
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-sm text-slate-900">{comment.userName}</div>
                          <div className="text-xs text-slate-500">
                            on <span className="font-medium text-slate-700">{comment.videoTitle || `Video #${comment.videoId}`}</span> · {new Date(comment.createdAt).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteComment(comment.id)}
                        className="text-slate-400 hover:text-red-600 h-7 w-7"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>

                    <p className="text-xs text-slate-700 mb-3 ml-12 leading-relaxed">{comment.text}</p>

                    <div className="flex items-center justify-between ml-12 text-xs text-slate-500">
                      <div className="flex items-center gap-4">
                        <button
                          onClick={() => handleToggleLike(comment.id)}
                          className={`flex items-center gap-1.5 font-medium transition-colors ${comment.isLiked ? "text-rose-600" : "hover:text-slate-900"}`}
                        >
                          <Heart className={`h-3.5 w-3.5 ${comment.isLiked ? "fill-rose-600 text-rose-600" : ""}`} />
                          {comment.likes}
                        </button>
                        <button
                          onClick={() => handleToggleReplies(comment.id)}
                          className="flex items-center gap-1.5 font-medium hover:text-slate-900 transition-colors"
                        >
                          <MessageCircle className="h-3.5 w-3.5" />
                          {comment.replyCount}
                        </button>
                      </div>

                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1 text-xs font-semibold text-slate-900 hover:text-slate-700 h-7 px-2"
                        onClick={() => {
                          setReplyOpenId(replyOpenId === comment.id ? null : comment.id);
                          setReplyText("");
                        }}
                      >
                        <CornerDownRight className="h-3 w-3" /> Reply
                      </Button>
                    </div>

                    {/* Inline reply composer */}
                    {replyOpenId === comment.id && (
                      <div className="mt-3 ml-12 flex gap-2">
                        <Input
                          placeholder={`Reply to ${comment.userName}…`}
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          className="flex-1 h-9 text-xs rounded-xl border-slate-200 bg-white"
                          autoFocus
                        />
                        <Button
                          size="sm"
                          disabled={!replyText.trim() || submittingReply}
                          onClick={() => handleSendReply(comment.id)}
                          className="bg-slate-900 text-white hover:bg-slate-800 rounded-xl shadow-xs"
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
                      <div className="mt-3 ml-12 pt-3 border-t border-slate-100 space-y-2">
                        {loadingReplies ? (
                          <div className="flex items-center gap-2 text-xs text-slate-400 py-2">
                            <Loader2 className="h-3.5 w-3.5 animate-spin text-slate-900" /> Loading replies...
                          </div>
                        ) : (repliesCache[comment.id] || []).length === 0 ? (
                          <p className="text-xs text-slate-400 py-1">No replies in this thread yet.</p>
                        ) : (
                          (repliesCache[comment.id] || []).map((reply) => {
                            const isSubReplyOpen = replyOpenId === `reply-${reply.id}`;
                            return (
                              <div key={reply.id} className="bg-slate-50/80 p-3 rounded-xl text-xs space-y-1.5 border border-slate-200/80">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-slate-900 flex items-center gap-1.5">
                                      {reply.userName}
                                      {reply.isCreator && (
                                        <Badge className="bg-slate-900 text-white text-[10px] px-1.5 py-0 rounded font-semibold border-0">
                                          Creator
                                        </Badge>
                                      )}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <span className="text-[10px] text-slate-400">{new Date(reply.createdAt).toLocaleDateString()}</span>
                                  </div>
                                </div>
                                <p className="text-slate-700 leading-relaxed whitespace-pre-line">{reply.text}</p>

                                {/* Subcomment stats and reply button bar */}
                                <div className="flex items-center justify-between pt-1 text-xs text-slate-500">
                                  <div className="flex items-center gap-4">
                                    <button
                                      type="button"
                                      onClick={() => handleToggleReplyLike(comment.id, reply.id)}
                                      className={`flex items-center gap-1.5 font-medium transition-colors cursor-pointer ${reply.isLiked ? "text-rose-600" : "hover:text-slate-900"}`}
                                    >
                                      <Heart className={`h-3 w-3 ${reply.isLiked ? "fill-rose-600 text-rose-600" : ""}`} />
                                      {reply.likes || 0}
                                    </button>
                                  </div>

                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 px-2 text-xs font-semibold text-slate-900 hover:text-slate-700 gap-1 cursor-pointer"
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
                                    <CornerDownRight className="h-3 w-3" /> Reply
                                  </Button>
                                </div>

                                {/* Inline sub-comment reply composer */}
                                {isSubReplyOpen && (
                                  <div className="mt-2 flex gap-2">
                                    <Input
                                      placeholder={`Reply to ${reply.userName}...`}
                                      value={replyText}
                                      onChange={(e) => setReplyText(e.target.value)}
                                      className="flex-1 h-8 text-xs bg-white border-slate-200 rounded-xl"
                                      autoFocus
                                    />
                                    <Button
                                      size="sm"
                                      disabled={!replyText.trim() || submittingReply}
                                      onClick={() => handleSendReply(comment.id, reply.id)}
                                      className="bg-slate-900 text-white hover:bg-slate-800 h-8 px-3 text-xs rounded-xl shadow-xs cursor-pointer font-semibold"
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
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-100">
                  <p className="text-xs text-slate-500 font-medium">
                    Page {page} of {totalPages}
                  </p>
                  <div className="flex items-center gap-1.5">
                    <Button variant="outline" size="icon" className="h-8 w-8 rounded-xl border-slate-200 hover:bg-slate-50 shadow-xs"
                      disabled={page === 1} onClick={() => setPage(page - 1)}>
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="icon" className="h-8 w-8 rounded-xl border-slate-200 hover:bg-slate-50 shadow-xs"
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
