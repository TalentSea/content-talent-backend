import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useNavigate } from "react-router";
import Hls from "hls.js";
import * as tus from "tus-js-client";
import {
  getVideos, getVideoDetails, initiateVideoUpload, updateVideo,
  deleteVideo, bulkDeleteVideos, publishVideo, scheduleVideo,
  uploadThumbnail, selectMainThumbnail, getPlaylists, getPlaylistDetails, createPlaylist, updatePlaylist,
  deletePlaylist, addVideosToPlaylist, removeVideoFromPlaylist,
  bulkRemoveVideosFromPlaylist, uploadPlaylistBanner, getPlaylistVideos,
  getAvailableVideosForPlaylist, reorderPlaylistVideos, getCategories,
  getAdminComments, postAdminVideoComment, getCommentReplies, postCommentReply,
  toggleCommentLike, deleteComment as apiDeleteComment, ApiVideo, ApiPlaylist, ApiComment, ApiReply
} from "../services/apiService";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Badge } from "../components/ui/badge";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "../components/ui/table";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "../components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "../components/ui/select";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import {
  Plus, Search, MoreVertical, Eye, Edit, Trash2, Upload,
  Video, FileText, X, Calendar, Clock, ListVideo,
  ChevronDown, ImagePlus, SlidersHorizontal, Play,
  ArrowLeft, Pencil, CheckSquare, RefreshCw, Loader2, AlertCircle, FolderOpen, CheckCircle,
  GripVertical, ArrowUp, ArrowDown, Download, Subtitles, Maximize2, Minimize2,
  MessageSquare, Send, Heart, CornerDownRight, MessageCircle
} from "lucide-react";


// ── Types ──────────────────────────────────────────────────────────────────

type Content = {
  id: number;
  title: string;
  type: string;
  category: string;
  status: string;
  views: string;
  duration: string;
  date: string;
  premium: boolean;
  description: string;
  tags: string[];
  thumbnailUrl?: string;
  videoUrl?: string;
  encodeProgress?: number;
  captionsData?: Array<{ srclang?: string; label?: string; is_default?: boolean; isDefault?: boolean; url?: string }>;
  captionUrl?: string;
  captionSrclang?: string;
  captionLabel?: string;
  downloadUrls?: Array<{ resolution: string; label: string; url: string }>;
};

type Playlist = {
  id: number;
  title: string;
  description: string;
  videos: number;
  videoIds: number[];
  date: string;
  thumbnailUrl?: string;
};

// ── Helpers ────────────────────────────────────────────────────────────────

function getOriginalVideoUrl(item: { videoUrl?: string; playbackUrl?: string; video_url?: string; url?: string }): string | undefined {
  if (!item) return undefined;
  return item.videoUrl || item.playbackUrl || (item as any).video_url || (item as any).url || (item as any).playback_url;
}

function formatDuration(val: any): string {
  if (!val || val === "0" || val === 0 || val === "0:00") {
    return "--:--";
  }
  if (typeof val === "number") {
    const mins = Math.floor(val / 60);
    const secs = Math.floor(val % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }
  if (typeof val === "string") {
    if (val.includes(":")) return val;
    const num = parseInt(val, 10);
    if (!isNaN(num) && num > 0) {
      const mins = Math.floor(num / 60);
      const secs = num % 60;
      return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
    }
  }
  return String(val);
}

function TagInput({ tags, setTags }: { tags: string[]; setTags: (t: string[]) => void }) {
  const [input, setInput] = useState("");
  const handleKey = (e: { key: string; preventDefault: () => void }) => {
    if ((e.key === "Enter" || e.key === " ") && input.trim()) {
      e.preventDefault();
      const tag = input.trim().replace(/^#/, "");
      if (tag && !tags.includes(tag)) setTags([...tags, tag]);
      setInput("");
    }
  };
  return (
    <div className="border border-slate-800 rounded-xl p-2 flex flex-wrap gap-1.5 min-h-[44px] focus-within:ring-2 focus-within:ring-purple-500/30 bg-slate-950/90 text-slate-100">
      {tags.map((t) => (
        <span key={t} className="inline-flex items-center gap-1 bg-purple-950/80 border border-purple-800/60 text-purple-300 text-xs font-medium px-2.5 py-1 rounded-full">
          #{t}
          <button type="button" onClick={() => setTags(tags.filter((x) => x !== t))} className="hover:text-rose-400"><X className="h-3 w-3" /></button>
        </span>
      ))}
      <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKey}
        placeholder={tags.length === 0 ? "Add tags (press Enter or Space)..." : ""}
        className="flex-1 min-w-[140px] text-sm outline-none bg-transparent text-slate-100 placeholder:text-slate-500 font-medium" />
    </div>
  );
}

function ThumbnailSlot({
  label,
  existingUrl,
  isMain,
  onSelect,
  onMakePrimary,
}: {
  label: string;
  existingUrl?: string;
  isMain?: boolean;
  onSelect?: (file: File) => void;
  onMakePrimary?: () => void;
}) {
  const [preview, setPreview] = useState<string | null>(existingUrl || null);

  useEffect(() => {
    setPreview(existingUrl || null);
  }, [existingUrl]);

  return (
    <div className={`relative border-2 ${isMain ? "border-purple-500 bg-purple-50/40" : "border-dashed border-slate-300 bg-slate-50"} rounded-xl overflow-hidden text-center transition-colors flex flex-col items-center justify-center p-2`}>
      <label className="cursor-pointer block w-full group">
        <input
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              const file = e.target.files[0];
              setPreview(URL.createObjectURL(file));
              if (onSelect) onSelect(file);
            }
          }}
        />
        {preview ? (
          <div className="relative w-full h-20 bg-slate-900 rounded-md overflow-hidden group">
            <img src={preview} alt={label} className="w-full h-full object-cover" />
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center transition-opacity text-white p-1">
              <ImagePlus className="h-4 w-4 mb-0.5 text-purple-300" />
              <span className="text-[10px] font-semibold">Change Image</span>
            </div>
          </div>
        ) : (
          <div className="p-2">
            <ImagePlus className="h-5 w-5 mx-auto text-slate-400 group-hover:text-purple-600 mb-1" />
            <p className="text-[11px] text-slate-500 group-hover:text-purple-600 font-medium">{label}</p>
          </div>
        )}
      </label>

      <div className="mt-1 flex items-center justify-between w-full px-1">
        <span className="text-[10px] font-semibold text-slate-600 truncate">{label}</span>
        {isMain ? (
          <span className="text-[9px] font-bold text-purple-700 bg-purple-100 px-1.5 py-0.5 rounded-full">Primary</span>
        ) : onMakePrimary && preview ? (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onMakePrimary();
            }}
            className="text-[9px] font-semibold text-purple-600 hover:text-purple-800 hover:underline"
          >
            Make Primary
          </button>
        ) : null}
      </div>
    </div>
  );
}

// ── Date range dialog ──────────────────────────────────────────────────────
function DateRangeDialog({ open, onClose, from, to, onChange }: {
  open: boolean; onClose: () => void;
  from: string; to: string;
  onChange: (from: string, to: string) => void;
}) {
  const [localFrom, setLocalFrom] = useState(from);
  const [localTo, setLocalTo] = useState(to);
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl">
        <DialogHeader>
          <DialogTitle>Filter by Date</DialogTitle>
          <DialogDescription>Select a single date or a date range</DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div>
            <Label className="text-sm">From Date</Label>
            <Input type="date" value={localFrom} onChange={(e) => setLocalFrom(e.target.value)} className="mt-1" />
          </div>
          <div>
            <Label className="text-sm">To Date <span className="text-gray-400 font-normal">(optional)</span></Label>
            <Input type="date" value={localTo} min={localFrom} onChange={(e) => setLocalTo(e.target.value)} className="mt-1" />
          </div>
          {localFrom && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 text-sm text-purple-700">
              {localTo && localTo !== localFrom
                ? <>Showing content from <strong>{localFrom}</strong> to <strong>{localTo}</strong></>
                : <>Showing content on <strong>{localFrom}</strong></>}
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { onChange("", ""); setLocalFrom(""); setLocalTo(""); onClose(); }}>Clear</Button>
          <Button onClick={() => { onChange(localFrom, localTo); onClose(); }}>Apply Filter</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Add Videos dialog (multi-select) ──────────────────────────────────────
function AddVideosDialog({ open, onClose, excludeIds, allVideos, playlistId, onAdd }: {
  open: boolean; onClose: () => void;
  excludeIds: number[];
  allVideos: Content[];
  playlistId?: number;
  onAdd: (ids: number[]) => void;
}) {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const [apiAvailable, setApiAvailable] = useState<Content[] | null>(null);

  useEffect(() => {
    if (open && playlistId) {
      getAvailableVideosForPlaylist(playlistId, { search })
        .then((res) => {
          const mapped: Content[] = res.data.map((item) => ({
            id: item.id,
            title: item.title,
            type: "Video",
            category: item.category || "Uncategorized",
            status: (item.status === "published" ? "Published" : item.status === "scheduled" ? "Scheduled" : "Draft") as any,
            views: item.views !== undefined ? item.views.toString() : "0",
            duration: item.duration || "0:00",
            date: item.date || new Date().toISOString().split("T")[0],
            premium: !!item.premium,
            description: item.description || "",
            tags: item.tags || [],
            thumbnailUrl: item.thumbnailUrl,
            captionsData: item.captionsData,
            captionUrl: item.captionUrl,
            captionSrclang: item.captionSrclang,
            captionLabel: item.captionLabel,
            downloadUrls: item.downloadUrls,
          }));
          setApiAvailable(mapped);
        })
        .catch((err) => {
          console.warn("Failed to fetch available videos for playlist", err);
          setApiAvailable(null);
        });
    } else {
      setApiAvailable(null);
    }
  }, [open, playlistId, search]);

  const available = apiAvailable !== null
    ? apiAvailable
    : allVideos.filter(
      (c) => !excludeIds.includes(c.id) &&
        c.title.toLowerCase().includes(search.toLowerCase())
    );

  const toggle = (id: number) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);

  const toggleAll = () =>
    setSelected(selected.length === available.length ? [] : available.map((v) => v.id));

  const handleAdd = () => {
    onAdd(selected);
    setSelected([]);
    setSearch("");
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={() => { setSelected([]); setSearch(""); onClose(); }}>
      <DialogContent className="max-w-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl">
        <DialogHeader>
          <DialogTitle>Add Videos to Playlist</DialogTitle>
          <DialogDescription>Select one or more videos to add</DialogDescription>
        </DialogHeader>
        <div className="space-y-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input placeholder="Search videos..." className="pl-9" value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>

          {available.length > 0 && (
            <div className="flex items-center gap-2 text-sm text-slate-500 pb-1 border-b">
              <input
                type="checkbox"
                className="h-4 w-4 rounded accent-purple-600"
                checked={selected.length === available.length && available.length > 0}
                onChange={toggleAll}
              />
              <span>Select all ({available.length})</span>
              {selected.length > 0 && <span className="text-purple-600 font-medium ml-auto">{selected.length} selected</span>}
            </div>
          )}

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {available.length === 0 ? (
              <p className="text-sm text-slate-400 text-center py-6">
                {search ? "No matching videos" : "No more videos to add"}
              </p>
            ) : (
              available.map((v) => (
                <label key={v.id} className={`flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-colors ${selected.includes(v.id) ? "border-purple-500 bg-purple-50" : "border-slate-200 hover:border-purple-300 hover:bg-slate-50"}`}>
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded accent-purple-600 flex-shrink-0"
                    checked={selected.includes(v.id)}
                    onChange={() => toggle(v.id)}
                  />
                  <div className="h-10 w-16 rounded bg-slate-900 flex items-center justify-center flex-shrink-0 relative overflow-hidden">
                    {v.thumbnailUrl ? (
                      <img src={v.thumbnailUrl} alt={v.title} className="w-full h-full object-cover" />
                    ) : (
                      <Video className="h-4 w-4 text-purple-400" />
                    )}
                    <span className="absolute bottom-0.5 right-0.5 text-white text-[10px] bg-black/70 px-1 rounded">{v.duration}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{v.title}</div>
                    <div className="text-xs text-slate-500">{v.category} · {v.date}</div>
                  </div>
                  <Badge variant={v.status === "Published" ? "default" : "secondary"} className="text-xs flex-shrink-0">{v.status}</Badge>
                </label>
              ))
            )}
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => { setSelected([]); setSearch(""); onClose(); }}>Cancel</Button>
          <Button disabled={selected.length === 0} onClick={handleAdd} className="gap-2 bg-slate-900 text-white hover:bg-slate-800">
            <Plus className="h-4 w-4" />Add Videos ({selected.length})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Select Playlist dialog (used inside upload dialog) ─────────────────────
function SelectPlaylistDialog({ open, onClose, playlists, selected, onToggle }: {
  open: boolean; onClose: () => void; playlists: Playlist[];
  selected: number[]; onToggle: (id: number) => void;
}) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-sm bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl">
        <DialogHeader>
          <DialogTitle>Add to Playlist</DialogTitle>
          <DialogDescription>Select one or more playlists for this video</DialogDescription>
        </DialogHeader>
        <div className="space-y-2 max-h-64 overflow-y-auto py-1">
          {playlists.length === 0 ? (
            <p className="text-sm text-slate-400 text-center py-4">No playlists yet</p>
          ) : (
            playlists.map((pl) => (
              <label key={pl.id} className={`flex items-center gap-3 p-2.5 rounded-lg border cursor-pointer transition-colors ${selected.includes(pl.id) ? "border-purple-500 bg-purple-50" : "border-slate-200 hover:bg-slate-50"}`}>
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded accent-purple-600 flex-shrink-0"
                  checked={selected.includes(pl.id)}
                  onChange={() => onToggle(pl.id)}
                />
                <div className="h-10 w-14 rounded bg-slate-900 flex items-center justify-center flex-shrink-0">
                  <ListVideo className="h-4 w-4 text-purple-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{pl.title}</div>
                  <div className="text-xs text-slate-500">{pl.videos} videos</div>
                </div>
              </label>
            ))
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={onClose} className="bg-slate-900 text-white hover:bg-slate-800">Done ({selected.length} selected)</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Upload / Edit video dialog ─────────────────────────────────────────────
function UploadEditDialog({ open, onClose, isEdit = false, content, playlists, onSaveSuccess }: {
  open: boolean;
  onClose: () => void;
  isEdit?: boolean;
  content?: Content;
  playlists: Playlist[];
  onSaveSuccess: () => void;
}) {
  const navigate = useNavigate();
  const [title, setTitle] = useState(content?.title || "");
  const [category, setCategory] = useState(content?.category || "");
  const [description, setDescription] = useState(content?.description || "");
  const [tags, setTags] = useState<string[]>(content?.tags ?? []);
  const [scheduleMode, setScheduleMode] = useState(false);
  const [scheduleDate, setScheduleDate] = useState("");
  const [scheduleTime, setScheduleTime] = useState("");
  const [selectedPlaylists, setSelectedPlaylists] = useState<number[]>([]);
  const [playlistPickerOpen, setPlaylistPickerOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [uploadProgress, setUploadProgress] = useState<number | null>(null);

  const [slot0File, setSlot0File] = useState<File | null>(null);
  const [slot1File, setSlot1File] = useState<File | null>(null);
  const [slot2File, setSlot2File] = useState<File | null>(null);

  const [videoFile, setVideoFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [dynamicCategories, setDynamicCategories] = useState<{ id: number; name: string }[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(false);

  useEffect(() => {
    setUploadProgress(null);
    if (open) {
      setLoadingCategories(true);
      getCategories({ simple: true })
        .then((cats) => {
          if (cats && Array.isArray(cats)) {
            setDynamicCategories(cats.map((c) => ({ id: c.id, name: c.name })));
          } else {
            setDynamicCategories([]);
          }
        })
        .catch((err) => {
          console.warn("Failed to load category list for upload form", err);
          setDynamicCategories([]);
        })
        .finally(() => {
          setLoadingCategories(false);
        });
    }
    if (content && open) {
      setTitle(content.title || "");
      setCategory(content.category || "");
      setDescription(content.description || "");
      setTags(content.tags || []);
      setVideoFile(null);
      setSlot0File(null);
      setSlot1File(null);
      setSlot2File(null);
      setError(null);

      // Fetch full video details from API to populate any missing past metadata
      getVideoDetails(content.id)
        .then((full) => {
          if (full) {
            if (full.title) setTitle(full.title);
            if (full.category) setCategory(full.category);
            if (full.description) setDescription(full.description);
            if (full.tags && Array.isArray(full.tags)) setTags(full.tags);
          }
        })
        .catch((err) => {
          console.warn("Could not fetch extended video details for edit form", err);
        });
    } else if (!content && open) {
      setTitle("");
      setCategory("");
      setDescription("");
      setTags([]);
      setSelectedPlaylists([]);
      setVideoFile(null);
      setSlot0File(null);
      setSlot1File(null);
      setSlot2File(null);
      setError(null);
    }
  }, [content?.id, open]);

  const togglePlaylist = (id: number) =>
    setSelectedPlaylists((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);

  const handleSave = async (statusArg: string) => {
    const status = statusArg.toLowerCase();
    setError(null);
    setUploadProgress(null);
    if (!title.trim()) {
      setError("Please enter a title for the video before saving.");
      return;
    }

    if (!isEdit && !videoFile) {
      setError("Please select a video file to upload.");
      return;
    }

    setSubmitting(true);
    try {
      if (isEdit && content) {
        // Editing existing content (e.g. Draft or Scheduled video -> Publish)
        await updateVideo(content.id, {
          title: title.trim(),
          category,
          description,
          tags,
          status,
        });

        if (slot0File) await uploadThumbnail(content.id, 0, slot0File);
        if (slot1File) await uploadThumbnail(content.id, 1, slot1File);
        if (slot2File) await uploadThumbnail(content.id, 2, slot2File);

        if (status === "published") {
          await publishVideo(content.id);
        } else if (status === "scheduled" && scheduleDate && scheduleTime) {
          await scheduleVideo(content.id, { date: scheduleDate, time: scheduleTime });
        }
      } else {
        // Creating NEW video upload
        const initRes = await initiateVideoUpload({
          title: title.trim(),
          filename: videoFile ? videoFile.name : "video.mp4",
          category,
          description,
          tags,
          status: status === "published" ? "pending" : status,
        });

        if (initRes.id) {
          if (slot0File) await uploadThumbnail(initRes.id, 0, slot0File);
          if (slot1File) await uploadThumbnail(initRes.id, 1, slot1File);
          if (slot2File) await uploadThumbnail(initRes.id, 2, slot2File);

          if (videoFile && initRes.signature) {
            try {
              await new Promise<void>((resolve) => {
                const upload = new tus.Upload(videoFile, {
                  endpoint: "https://video.bunnycdn.com/tusupload",
                  storeFingerprintForResuming: false,
                  removeFingerprintOnSuccess: true,
                  retryDelays: [0, 3000, 5000],
                  chunkSize: 5 * 1024 * 1024,
                  uploadSize: videoFile.size,
                  headers: {
                    AuthorizationSignature: String(initRes.signature),
                    AuthorizationExpire: String(initRes.expirationTime || Math.floor(Date.now() / 1000) + 3600),
                    VideoId: String(initRes.bunnyVideoId || initRes.id),
                    LibraryId: String(initRes.bunnyLibraryId || "123456"),
                  },
                  metadata: {
                    filetype: videoFile.type || "video/mp4",
                    title: title.trim(),
                  },
                  onProgress: (bytesUploaded, bytesTotal) => {
                    if (bytesTotal > 0) {
                      const pct = Math.round((bytesUploaded / bytesTotal) * 100);
                      setUploadProgress(pct);
                    }
                  },
                  onError: (err) => {
                    console.warn("TUS stream notice:", err);
                    resolve();
                  },
                  onSuccess: () => {
                    console.log("TUS binary stream uploaded successfully!");
                    setUploadProgress(100);
                    resolve();
                  },
                });
                upload.start();
              });
            } catch (tErr) {
              console.warn("TUS background stream exception:", tErr);
            }
          }

          if (status === "scheduled" && scheduleDate && scheduleTime) {
            await scheduleVideo(initRes.id, { date: scheduleDate, time: scheduleTime });
          }

          for (const plId of selectedPlaylists) {
            await addVideosToPlaylist(plId, [initRes.id]);
          }
        }
      }
      onSaveSuccess();
      onClose();
    } catch (err: any) {
      console.error("Failed to save video asset:", err);
      setError(err?.message || "An error occurred while saving the video asset. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <SelectPlaylistDialog
        open={playlistPickerOpen}
        onClose={() => setPlaylistPickerOpen(false)}
        playlists={playlists}
        selected={selectedPlaylists}
        onToggle={togglePlaylist}
      />
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl">
          <DialogHeader>
            <DialogTitle>{isEdit ? "Edit Content Details" : "Upload New Content"}</DialogTitle>
            <DialogDescription>{isEdit ? "Update your content details below" : "Add new video asset to your platform"}</DialogDescription>
          </DialogHeader>

          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl font-medium">
              {error}
            </div>
          )}

          {uploadProgress !== null && (
            <div className="p-3 text-xs bg-purple-50 border border-purple-200 rounded-xl space-y-1.5">
              <div className="flex items-center justify-between font-semibold text-purple-900">
                <span className="flex items-center gap-1.5">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-600" />
                  Streaming binary upload via TUS...
                </span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-purple-200 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-purple-600 h-full transition-all duration-300 rounded-full"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <div className="space-y-5">
            <div><Label>Title</Label><Input placeholder="Enter content title" value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1" /></div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <Label>Category</Label>
                {dynamicCategories.length > 0 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      onClose();
                      navigate("/categories");
                    }}
                    className="h-6 text-xs gap-1 text-purple-400 hover:text-purple-300 hover:bg-purple-950/40 px-2 py-0 font-medium"
                  >
                    <Plus className="h-3 w-3" />
                    New Category
                  </Button>
                )}
              </div>

              {loadingCategories ? (
                <div className="flex items-center gap-2 p-2.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950/60 text-xs text-slate-400 mt-1">
                  <Loader2 className="h-3.5 w-3.5 animate-spin text-purple-500" />
                  Loading categories...
                </div>
              ) : dynamicCategories.length === 0 ? (
                <div className="flex items-center justify-between p-3 rounded-xl border border-dashed border-purple-500/40 bg-purple-950/20 text-xs text-slate-300 gap-3 mt-1">
                  <span className="text-slate-300">
                    No categories found. Please create a category first to organize your video content.
                  </span>
                  <Button
                    type="button"
                    size="sm"
                    className="gap-1 bg-purple-600 hover:bg-purple-500 text-white shrink-0 font-medium h-8 text-xs shadow-md shadow-purple-600/30"
                    onClick={() => {
                      onClose();
                      navigate("/categories");
                    }}
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Add Category
                  </Button>
                </div>
              ) : (
                <Select
                  value={category ? category.toLowerCase() : ""}
                  onValueChange={(val) => {
                    const matched = dynamicCategories.find((c) => c.name.toLowerCase() === val);
                    setCategory(matched ? matched.name : val);
                  }}
                >
                  <SelectTrigger className="mt-1 bg-white dark:bg-slate-950 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent className="bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100">
                    {dynamicCategories.map((c) => (
                      <SelectItem key={c.id} value={c.name.toLowerCase()}>
                        {c.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
            <div><Label>Description</Label><Textarea placeholder="Enter content description" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} className="mt-1" /></div>
            <div>
              <Label>Thumbnails</Label>
              <p className="text-xs text-slate-500 mb-2">Upload custom thumbnail images.</p>
              <div className="grid grid-cols-3 gap-3">
                <ThumbnailSlot
                  label="Thumbnail 1"
                  isMain={true}
                  existingUrl={content?.thumbnailUrl || (content as any)?.mainThumbnailUrl || (content as any)?.main_thumbnail_url}
                  onSelect={(f) => {
                    setSlot0File(f);
                    if (content) uploadThumbnail(content.id, 0, f);
                  }}
                />
                <ThumbnailSlot
                  label="Thumbnail 2"
                  existingUrl={(content as any)?.altThumbnailUrls?.[0] || (content as any)?.alt_thumbnail_urls?.[0]}
                  onSelect={(f) => {
                    setSlot1File(f);
                    if (content) uploadThumbnail(content.id, 1, f);
                  }}
                  onMakePrimary={() => {
                    if (content) {
                      const url = (content as any)?.altThumbnailUrls?.[0] || (content as any)?.alt_thumbnail_urls?.[0] || 1;
                      selectMainThumbnail(content.id, url).then(() => onSaveSuccess());
                    }
                  }}
                />
                <ThumbnailSlot
                  label="Thumbnail 3"
                  existingUrl={(content as any)?.altThumbnailUrls?.[1] || (content as any)?.alt_thumbnail_urls?.[1]}
                  onSelect={(f) => {
                    setSlot2File(f);
                    if (content) uploadThumbnail(content.id, 2, f);
                  }}
                  onMakePrimary={() => {
                    if (content) {
                      const url = (content as any)?.altThumbnailUrls?.[1] || (content as any)?.alt_thumbnail_urls?.[1] || 2;
                      selectMainThumbnail(content.id, url).then(() => onSaveSuccess());
                    }
                  }}
                />
              </div>
            </div>
            <div>
              <Label>Tags</Label>
              <p className="text-xs text-slate-500 mb-1.5">Help viewers discover your content</p>
              <TagInput tags={tags} setTags={setTags} />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <Label>Playlists</Label>
                <Button variant="outline" size="sm" className="gap-1.5 h-7 text-xs" onClick={() => setPlaylistPickerOpen(true)}>
                  <ListVideo className="h-3.5 w-3.5" />Add to Playlist
                </Button>
              </div>
              {selectedPlaylists.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {playlists.filter((p) => selectedPlaylists.includes(p.id)).map((p) => (
                    <span key={p.id} className="inline-flex items-center gap-1 bg-purple-100 text-purple-700 text-xs font-medium px-2.5 py-1 rounded-full">
                      {p.title}
                      <button type="button" onClick={() => togglePlaylist(p.id)} className="hover:text-red-500"><X className="h-3 w-3" /></button>
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-slate-400">Not added to any playlist</p>
              )}
            </div>

            {!isEdit && (
              <div>
                <Label>Video File</Label>
                <input
                  type="file"
                  ref={fileInputRef}
                  accept="video/mp4,video/mov,video/avi,video/*"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      const file = e.target.files[0];
                      setVideoFile(file);
                      if (!title) {
                        setTitle(file.name.replace(/\.[^/.]+$/, ""));
                      }
                    }
                  }}
                />

                {videoFile ? (
                  <div className="mt-1.5 border-2 border-purple-200 bg-purple-50/60 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="h-10 w-10 rounded-lg bg-purple-600 flex items-center justify-center text-white flex-shrink-0">
                        <Video className="h-5 w-5" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-900 truncate">{videoFile.name}</p>
                        <p className="text-xs text-slate-500">{(videoFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      type="button"
                      className="text-slate-500 hover:text-red-600 hover:bg-red-50 h-8 px-2"
                      onClick={() => setVideoFile(null)}
                    >
                      <X className="h-4 w-4 mr-1" /> Remove
                    </Button>
                  </div>
                ) : (
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => {
                      e.preventDefault();
                      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        const file = e.dataTransfer.files[0];
                        setVideoFile(file);
                        if (!title) {
                          setTitle(file.name.replace(/\.[^/.]+$/, ""));
                        }
                      }
                    }}
                    className="mt-1.5 border-2 border-dashed border-slate-300 rounded-xl p-6 text-center bg-slate-50 hover:border-purple-500 hover:bg-purple-50/30 transition-all cursor-pointer group block"
                  >
                    <Upload className="h-10 w-10 mx-auto text-slate-400 group-hover:text-purple-600 mb-2 transition-colors" />
                    <p className="text-sm font-medium text-slate-700 group-hover:text-purple-700 mb-1">Drag & drop your video file here</p>
                    <p className="text-xs text-slate-400 mb-3">Supports MP4, MOV, AVI up to 4GB</p>
                    <Button
                      variant="outline"
                      size="sm"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        fileInputRef.current?.click();
                      }}
                      className="bg-white hover:bg-slate-100 border-slate-300 text-slate-800 font-medium shadow-xs"
                    >
                      <FolderOpen className="h-3.5 w-3.5 mr-1.5 text-purple-600" /> Browse Files
                    </Button>
                  </div>
                )}
              </div>
            )}

            {scheduleMode && (
              <div className="border border-purple-200 bg-purple-50 rounded-xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-purple-700 font-medium text-sm">
                    <Calendar className="h-4 w-4" />Schedule Publishing Date
                  </div>
                  <button type="button" onClick={() => setScheduleMode(false)} className="text-slate-400 hover:text-slate-600">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div><Label>Date</Label><Input type="date" value={scheduleDate} onChange={(e) => setScheduleDate(e.target.value)} className="mt-1" /></div>
                  <div><Label>Time</Label><Input type="time" value={scheduleTime} onChange={(e) => setScheduleTime(e.target.value)} className="mt-1" /></div>
                </div>
              </div>
            )}
          </div>
          <DialogFooter className="mt-4 gap-2">
            {isEdit ? (
              <>
                <Button variant="outline" onClick={onClose} disabled={submitting}>
                  Cancel
                </Button>
                <Button
                  className="bg-purple-600 hover:bg-purple-500 text-white font-medium px-5 cursor-pointer"
                  onClick={() => handleSave(content?.status || "published")}
                  disabled={submitting}
                >
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin mr-1.5" /> : null}
                  Save
                </Button>
              </>
            ) : (
              <>
                <Button variant="outline" onClick={onClose} disabled={submitting}>Cancel</Button>
                <Button variant="outline" onClick={() => handleSave("draft")} disabled={submitting}>
                  {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save as Draft"}
                </Button>
                {scheduleMode ? (
                  <Button
                    disabled={!scheduleDate || !scheduleTime || submitting}
                    onClick={() => handleSave("scheduled")}
                    className="gap-2 bg-slate-900 text-white hover:bg-slate-800"
                  >
                    {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calendar className="h-4 w-4" />}
                    Confirm Schedule
                  </Button>
                ) : (
                  <div className="flex">
                    <Button className="rounded-r-none bg-slate-900 hover:bg-slate-800 text-white" onClick={() => handleSave("published")} disabled={submitting}>
                      {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Publish"}
                    </Button>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild disabled={submitting}>
                        <Button className="rounded-l-none px-2 bg-slate-950 hover:bg-black text-white border-l border-slate-800"><ChevronDown className="h-4 w-4" /></Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleSave("published")}><Video className="mr-2 h-4 w-4" />Publish Now</DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => setScheduleMode(true)}><Clock className="mr-2 h-4 w-4" />Schedule Publish</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                )}
              </>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

// ── Edit video details dialog ──────────────────────────────────────────────
function EditVideoDialog({ open, onClose, content, playlists, onSaveSuccess }: {
  open: boolean; onClose: () => void; content: Content | null; playlists: Playlist[]; onSaveSuccess: () => void;
}) {
  if (!content) return null;
  return <UploadEditDialog open={open} onClose={onClose} isEdit content={content} playlists={playlists} onSaveSuccess={onSaveSuccess} />;
}

// ── Create / Edit Playlist metadata dialog ─────────────────────────────────
function PlaylistMetaDialog({ open, onClose, playlist, allVideos, onSaveSuccess }: {
  open: boolean;
  onClose: () => void;
  playlist?: Playlist;
  allVideos: Content[];
  onSaveSuccess: () => void;
}) {
  const isEdit = !!playlist;
  const [title, setTitle] = useState(playlist?.title || "");
  const [description, setDescription] = useState(playlist?.description || "");
  const [thumbnailUrl, setThumbnailUrl] = useState<string | undefined>(playlist?.thumbnailUrl);
  const [videoIds, setVideoIds] = useState<number[]>(playlist?.videoIds ?? []);
  const [playlistVideosList, setPlaylistVideosList] = useState<Content[]>([]);
  const [addVideosOpen, setAddVideosOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loadingData, setLoadingData] = useState(false);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const bannerFileRef = useRef<HTMLInputElement | null>(null);

  // Fetch playlist details & videos from API when editing
  useEffect(() => {
    if (open && playlist) {
      setTitle(playlist.title || "");
      setDescription(playlist.description || "");
      setThumbnailUrl(playlist.thumbnailUrl);
      const initialIds = playlist.videoIds || [];
      setVideoIds(initialIds);

      const loadFullDetails = async () => {
        setLoadingData(true);
        try {
          let currentVideoIds = [...initialIds];

          // Fetch playlist videos API
          let fetchedVideos: Content[] = [];
          try {
            const videosRes = await getPlaylistVideos(playlist.id);
            if (videosRes?.data && Array.isArray(videosRes.data) && videosRes.data.length > 0) {
              fetchedVideos = videosRes.data.map((item: ApiVideo) => ({
                id: item.id,
                title: item.title,
                type: "Video",
                category: item.category || "Uncategorized",
                status: item.status ? item.status.charAt(0).toUpperCase() + item.status.slice(1) : "Draft",
                views: item.views !== undefined ? item.views.toString() : "0",
                duration: item.duration || "0:00",
                date: item.date || new Date().toISOString().split("T")[0],
                premium: !!item.premium,
                description: item.description || "",
                tags: item.tags || [],
                thumbnailUrl: item.thumbnailUrl,
                captionsData: item.captionsData,
                captionUrl: item.captionUrl,
                captionSrclang: item.captionSrclang,
                captionLabel: item.captionLabel,
                downloadUrls: item.downloadUrls,
              }));
            }
          } catch (e) {
            console.warn("getPlaylistVideos failed in dialog, using local fallback", e);
          }

          // Fallback to allVideos filtered by currentVideoIds if API returned empty
          if (fetchedVideos.length === 0 && currentVideoIds.length > 0) {
            fetchedVideos = allVideos.filter((c) => currentVideoIds.includes(c.id));
          }

          setPlaylistVideosList(fetchedVideos);

          const combinedIds = Array.from(
            new Set([...currentVideoIds, ...fetchedVideos.map((v) => v.id)])
          );
          setVideoIds(combinedIds);
        } catch (err) {
          console.warn("Failed to load playlist details in edit dialog:", err);
          const fallback = allVideos.filter((c) => (playlist.videoIds || []).includes(c.id));
          setPlaylistVideosList(fallback);
          setVideoIds(fallback.map((v) => v.id));
        } finally {
          setLoadingData(false);
        }
      };

      loadFullDetails();
    } else if (open) {
      setTitle("");
      setDescription("");
      setThumbnailUrl(undefined);
      setVideoIds([]);
      setPlaylistVideosList([]);
    }
  }, [playlist, open, allVideos]);

  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // Combine fetched videos with allVideos state for rendering list in dialog (in exact videoIds order)
  const displayedVideos = useMemo(() => {
    const map = new Map<number, Content>();

    // 1. Include all videos fetched from playlist
    playlistVideosList.forEach((v) => map.set(v.id, v));

    // 2. Include any videos from allVideos matching videoIds
    allVideos.forEach((v) => {
      if (videoIds.includes(v.id) && !map.has(v.id)) {
        map.set(v.id, v);
      }
    });

    // 3. Respect order specified by videoIds
    if (videoIds.length > 0) {
      const ordered: Content[] = [];
      videoIds.forEach((id) => {
        const item = map.get(id);
        if (item) ordered.push(item);
      });
      map.forEach((item, id) => {
        if (!videoIds.includes(id)) ordered.push(item);
      });
      return ordered;
    }
    return Array.from(map.values());
  }, [playlistVideosList, allVideos, videoIds]);

  const moveVideo = async (fromIndex: number, toIndex: number) => {
    if (fromIndex < 0 || fromIndex >= displayedVideos.length) return;
    if (toIndex < 0 || toIndex >= displayedVideos.length) return;
    if (fromIndex === toIndex) return;

    const newDisplayed = [...displayedVideos];
    const [movedItem] = newDisplayed.splice(fromIndex, 1);
    newDisplayed.splice(toIndex, 0, movedItem);

    const newIds = newDisplayed.map((v) => v.id);
    setVideoIds(newIds);
    setPlaylistVideosList(newDisplayed);

    if (isEdit && playlist) {
      try {
        const payload = newIds.map((id, idx) => ({ video_id: id, order: idx + 1 }));
        await reorderPlaylistVideos(playlist.id, payload);
      } catch (err) {
        console.error("Failed to reorder playlist videos:", err);
      }
    }
  };

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadingBanner(true);
      try {
        if (playlist) {
          const res = await uploadPlaylistBanner(playlist.id, file);
          if (res && (res as any).thumbnailUrl) {
            setThumbnailUrl((res as any).thumbnailUrl);
          } else if (res && (res as any).bannerUrl) {
            setThumbnailUrl((res as any).bannerUrl);
          } else {
            setThumbnailUrl(URL.createObjectURL(file));
          }
        } else {
          setThumbnailUrl(URL.createObjectURL(file));
        }
      } catch (err) {
        console.error("Failed to upload thumbnail in edit dialog:", err);
      } finally {
        setUploadingBanner(false);
      }
    }
  };

  const handleRemoveVideo = async (id: number) => {
    setVideoIds((prev) => prev.filter((x) => x !== id));
    setPlaylistVideosList((prev) => prev.filter((x) => x.id !== id));
    if (isEdit && playlist) {
      try {
        await removeVideoFromPlaylist(playlist.id, id);
      } catch (err) {
        console.error("Failed to remove video from playlist:", err);
      }
    }
  };

  const handleAddVideos = async (newIds: number[]) => {
    const filtered = newIds.filter((id) => !videoIds.includes(id));
    if (filtered.length === 0) return;
    setVideoIds((prev) => [...prev, ...filtered]);
    if (isEdit && playlist) {
      try {
        await addVideosToPlaylist(playlist.id, filtered);
      } catch (err) {
        console.error("Failed to add videos to playlist:", err);
      }
    }
  };

  const handleSave = async () => {
    if (!title.trim()) return;
    setSubmitting(true);
    try {
      if (isEdit && playlist) {
        await updatePlaylist(playlist.id, { title, description });
      } else {
        const newPl = await createPlaylist({ title, description, videoIds });
        if (newPl && newPl.id && bannerFileRef.current?.files?.[0]) {
          try {
            await uploadPlaylistBanner(newPl.id, bannerFileRef.current.files[0]);
          } catch (e) {
            console.warn("Failed to upload banner for new playlist:", e);
          }
        }
      }
      onSaveSuccess();
      onClose();
    } catch (err) {
      console.error("Failed to save playlist:", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <AddVideosDialog
        open={addVideosOpen}
        onClose={() => setAddVideosOpen(false)}
        excludeIds={videoIds}
        allVideos={allVideos}
        onAdd={handleAddVideos}
      />
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 text-slate-100 shadow-2xl backdrop-blur-xl">
          <DialogHeader>
            <DialogTitle className="text-xl font-bold text-slate-100">
              {isEdit ? "Edit Playlist Details" : "Create New Playlist"}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {isEdit ? "Update playlist info, thumbnail image, and manage video collection" : "Create a new structured video collection"}
            </DialogDescription>
          </DialogHeader>

          {loadingData ? (
            <div className="py-12 flex items-center justify-center gap-3 text-purple-400">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="text-sm font-medium text-slate-300">Fetching playlist details...</span>
            </div>
          ) : (
            <div className="space-y-5 py-2">
              {/* Thumbnail Section */}
              <div>
                <Label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2 block">Playlist Thumbnail</Label>
                <input
                  type="file"
                  ref={bannerFileRef}
                  accept="image/*"
                  className="hidden"
                  onChange={handleBannerUpload}
                />

                {thumbnailUrl ? (
                  <div className="relative border border-slate-800 bg-slate-950 rounded-2xl h-44 overflow-hidden group shadow-lg">
                    <img src={thumbnailUrl} alt="Playlist thumbnail" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                    <div
                      onClick={() => bannerFileRef.current?.click()}
                      className="absolute inset-0 bg-slate-950/80 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-white gap-2 font-semibold text-xs cursor-pointer backdrop-blur-xs"
                    >
                      {uploadingBanner ? (
                        <>
                          <Loader2 className="h-7 w-7 animate-spin text-purple-400" />
                          <span>Uploading Thumbnail...</span>
                        </>
                      ) : (
                        <>
                          <div className="h-10 w-10 rounded-full bg-purple-600/90 flex items-center justify-center shadow-lg">
                            <ImagePlus className="h-5 w-5 text-white" />
                          </div>
                          <span>Change Playlist Thumbnail</span>
                        </>
                      )}
                    </div>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => bannerFileRef.current?.click()}
                    disabled={uploadingBanner}
                    className="w-full border-2 border-dashed border-slate-800 bg-slate-950/60 hover:bg-slate-950 hover:border-purple-500/80 rounded-2xl h-36 flex flex-col items-center justify-center cursor-pointer transition-all group p-4 text-center"
                  >
                    {uploadingBanner ? (
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="h-7 w-7 animate-spin text-purple-400" />
                        <span className="text-xs text-slate-300">Uploading Thumbnail...</span>
                      </div>
                    ) : (
                      <>
                        <div className="h-10 w-10 rounded-full bg-purple-950/80 border border-purple-800/60 flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
                          <ImagePlus className="h-5 w-5 text-purple-400" />
                        </div>
                        <p className="text-xs text-slate-200 group-hover:text-purple-400 font-semibold">Click to upload playlist thumbnail</p>
                        <p className="text-[11px] text-slate-500 mt-1">Recommended resolution: 1280×720 (16:9 ratio)</p>
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Title Input */}
              <div>
                <Label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5 block">Title</Label>
                <Input
                  placeholder="e.g. React Masterclass Series"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-500 focus:border-purple-500"
                />
              </div>

              {/* Description Input */}
              <div>
                <Label className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1.5 block">Description</Label>
                <Textarea
                  placeholder="Describe what this playlist covers..."
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="bg-slate-950 border-slate-800 text-slate-100 placeholder:text-slate-500 focus:border-purple-500 resize-none"
                />
              </div>

              {/* Videos List Section inside Edit Dialog */}
              <div>
                <div className="flex items-center justify-between mb-2.5">
                  <div>
                    <Label className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
                      Playlist Videos ({displayedVideos.length})
                    </Label>
                    <span className="text-[11px] text-slate-500 font-normal">
                      Drag handle or use arrows to change order
                    </span>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 h-8 text-xs bg-slate-950 border-slate-800 hover:bg-slate-800 text-slate-200 cursor-pointer"
                    onClick={() => setAddVideosOpen(true)}
                  >
                    <Plus className="h-3.5 w-3.5 text-purple-400" /> Add Videos
                  </Button>
                </div>

                {displayedVideos.length === 0 ? (
                  <div className="border border-dashed border-slate-800 rounded-xl p-6 text-center bg-slate-950/60">
                    <Video className="h-8 w-8 mx-auto mb-2 text-slate-600" />
                    <p className="text-xs text-slate-400 font-medium">No videos added to this playlist yet</p>
                    <Button variant="link" size="sm" className="text-xs text-purple-400 mt-1 cursor-pointer" onClick={() => setAddVideosOpen(true)}>
                      Add videos now
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {displayedVideos.map((v, index) => (
                      <div
                        key={v.id}
                        draggable
                        onDragStart={(e) => {
                          setDraggedIndex(index);
                          e.dataTransfer.effectAllowed = "move";
                        }}
                        onDragOver={(e) => {
                          e.preventDefault();
                          e.dataTransfer.dropEffect = "move";
                        }}
                        onDrop={(e) => {
                          e.preventDefault();
                          if (draggedIndex !== null && draggedIndex !== index) {
                            moveVideo(draggedIndex, index);
                          }
                          setDraggedIndex(null);
                        }}
                        onDragEnd={() => setDraggedIndex(null)}
                        className={`flex items-center gap-2.5 p-2.5 bg-slate-950/80 rounded-xl border transition-all group ${draggedIndex === index
                          ? "border-purple-500 bg-purple-950/40 opacity-50"
                          : "border-slate-800/80 hover:border-slate-700"
                          }`}
                      >
                        {/* Drag Handle & Order */}
                        <div className="flex items-center gap-1.5 text-slate-500">
                          <GripVertical className="h-4 w-4 text-slate-500 cursor-grab hover:text-purple-400 transition-colors" />
                          <span className="w-5 text-center text-xs font-mono font-bold text-slate-500">#{index + 1}</span>
                        </div>

                        {/* Thumbnail */}
                        <div className="h-10 w-16 rounded-lg bg-slate-900 border border-slate-800 overflow-hidden flex items-center justify-center flex-shrink-0 relative">
                          {v.thumbnailUrl ? (
                            <img src={v.thumbnailUrl} alt={v.title} className="w-full h-full object-cover" />
                          ) : (
                            <Video className="h-4 w-4 text-purple-400 opacity-70" />
                          )}
                          <span className="absolute bottom-0.5 right-0.5 bg-black/80 text-[9px] text-white px-1 rounded font-mono">{v.duration}</span>
                        </div>

                        {/* Title & Info */}
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-bold text-slate-200 truncate group-hover:text-purple-400 transition-colors">{v.title}</div>
                          <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                            <span>{v.category}</span>
                            <span>•</span>
                            <span>{v.views || "0"} views</span>
                          </div>
                        </div>

                        {/* Up / Down Controls & Delete */}
                        <div className="flex items-center gap-1">
                          <button
                            type="button"
                            disabled={index === 0}
                            onClick={() => moveVideo(index, index - 1)}
                            className="h-7 w-7 rounded-lg text-slate-400 hover:text-purple-400 hover:bg-slate-800 disabled:opacity-25 disabled:hover:bg-transparent disabled:hover:text-slate-400 flex items-center justify-center transition-colors cursor-pointer"
                            title="Move video up"
                          >
                            <ArrowUp className="h-3.5 w-3.5" />
                          </button>

                          <button
                            type="button"
                            disabled={index === displayedVideos.length - 1}
                            onClick={() => moveVideo(index, index + 1)}
                            className="h-7 w-7 rounded-lg text-slate-400 hover:text-purple-400 hover:bg-slate-800 disabled:opacity-25 disabled:hover:bg-transparent disabled:hover:text-slate-400 flex items-center justify-center transition-colors cursor-pointer"
                            title="Move video down"
                          >
                            <ArrowDown className="h-3.5 w-3.5" />
                          </button>

                          <button
                            type="button"
                            onClick={() => handleRemoveVideo(v.id)}
                            className="h-7 w-7 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 flex items-center justify-center transition-colors cursor-pointer ml-0.5"
                            title="Remove video from playlist"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <DialogFooter className="mt-4 pt-3 border-t border-slate-800/80">
            <Button variant="outline" onClick={onClose} disabled={submitting} className="bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800 cursor-pointer">
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={submitting || !title.trim()} className="bg-purple-600 hover:bg-purple-500 text-white font-medium cursor-pointer">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : isEdit ? "Save Changes" : "Create Playlist"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

interface VttCue {
  start: number;
  end: number;
  text: string;
}

function parseTimeToSeconds(timeStr: string): number {
  if (!timeStr) return 0;
  const parts = timeStr.trim().split(":");
  let hours = 0, minutes = 0, seconds = 0;
  if (parts.length === 3) {
    hours = parseFloat(parts[0]) || 0;
    minutes = parseFloat(parts[1]) || 0;
    seconds = parseFloat(parts[2].replace(",", ".")) || 0;
  } else if (parts.length === 2) {
    minutes = parseFloat(parts[0]) || 0;
    seconds = parseFloat(parts[1].replace(",", ".")) || 0;
  } else {
    seconds = parseFloat(parts[0]) || 0;
  }
  return hours * 3600 + minutes * 60 + seconds;
}

export interface CaptionTrack {
  srclang: string;
  label: string;
  url: string;
}

// ── HLS Video Player helper component ─────────────────────────────────────
function HlsVideoPlayer({
  videoSrc,
  poster,
  captions = [],
  selectedTrackUrl = null,
  onLoadedMetadata,
  onError,
}: {
  videoSrc: string;
  poster?: string;
  captions?: CaptionTrack[];
  selectedTrackUrl?: string | null;
  onLoadedMetadata?: (e: React.SyntheticEvent<HTMLVideoElement, Event>) => void;
  onError?: () => void;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const selectedTrack = captions.find((c) => c.url === selectedTrackUrl);

  // Sync textTrack modes dynamically when selectedTrackUrl is changed
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !selectedTrackUrl) return;

    const syncTracks = () => {
      if (video.textTracks && video.textTracks.length > 0) {
        for (let i = 0; i < video.textTracks.length; i++) {
          const track = video.textTracks[i];
          const isMatch = !!(
            (track as any).src === selectedTrackUrl ||
            track.language === selectedTrack?.srclang ||
            track.label === selectedTrack?.label ||
            (selectedTrack?.srclang && track.language && track.language.toLowerCase().startsWith(selectedTrack.srclang.toLowerCase()))
          );

          if (isMatch && track.mode !== "showing") {
            track.mode = "showing";
          }
        }
      }
    };

    syncTracks();
    video.addEventListener("loadedmetadata", syncTracks);
    video.addEventListener("play", syncTracks);

    return () => {
      video.removeEventListener("loadedmetadata", syncTracks);
      video.removeEventListener("play", syncTracks);
    };
  }, [selectedTrackUrl, selectedTrack]);

  // HLS stream attach - strictly depends ONLY on videoSrc so video never reloads on UI state updates
  useEffect(() => {
    const video = videoRef.current;
    if (!video || !videoSrc) return;

    let hls: Hls | null = null;

    if (videoSrc.includes(".m3u8") && Hls.isSupported()) {
      hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        renderTextTracksNatively: true,
      });
      hls.loadSource(videoSrc);
      hls.attachMedia(video);
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => { });
      });
      hls.on(Hls.Events.ERROR, (_event, data) => {
        if (data.fatal && onErrorRef.current) {
          onErrorRef.current();
        }
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl") || !videoSrc.includes(".m3u8")) {
      video.src = videoSrc;
      video.play().catch(() => { });
    } else if (onErrorRef.current) {
      onErrorRef.current();
    }

    return () => {
      if (hls) {
        hls.destroy();
      }
    };
  }, [videoSrc]);

  return (
    <div className="relative w-full h-full flex items-center justify-center bg-black overflow-hidden group select-none">
      <video
        ref={videoRef}
        controls
        autoPlay
        playsInline
        crossOrigin="anonymous"
        poster={poster}
        onLoadedMetadata={onLoadedMetadata}
        onError={onError}
        className="w-full h-full object-contain max-w-full max-h-full"
        style={{ width: "100%", height: "100%", objectFit: "contain" }}
      >
        {captions.map((c) => (
          <track
            key={c.url}
            kind="subtitles"
            src={c.url}
            srcLang={c.srclang || "en"}
            label={c.label || "Subtitles"}
          />
        ))}
      </video>
    </div>
  );
}

// ── Video Player dialog ───────────────────────────────────────────────────
function VideoPlayerDialog({ open, onClose, content, onPlaybackError }: {
  open: boolean; onClose: () => void; content: Content | null; onPlaybackError?: (msg: string) => void;
}) {
  const playerContainerRef = useRef<HTMLDivElement | null>(null);
  const [playbackError, setPlaybackError] = useState(false);
  const [fetchedUrl, setFetchedUrl] = useState<string | null>(null);
  const [loadingStream, setLoadingStream] = useState(false);
  const [dynamicDuration, setDynamicDuration] = useState<string | null>(null);
  const [videoAspectRatio, setVideoAspectRatio] = useState<string>("16/9");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [selectedTrackUrl, setSelectedTrackUrl] = useState<string | null>(null);
  const [isCcMenuOpen, setIsCcMenuOpen] = useState(false);

  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null);
  const [isDownloadMenuOpen, setIsDownloadMenuOpen] = useState(false);
  const [fetchedDetails, setFetchedDetails] = useState<ApiVideo | null>(null);
  const fetchedVideoIdRef = useRef<number | null>(null);

  // Comments state inside VideoPlayerDialog
  const [videoComments, setVideoComments] = useState<ApiComment[]>([]);
  const [loadingVideoComments, setLoadingVideoComments] = useState(false);
  const [adminCommentText, setAdminCommentText] = useState("");
  const [postingAdminComment, setPostingAdminComment] = useState(false);

  // Thread reply states
  const [replyOpenId, setReplyOpenId] = useState<number | string | null>(null);
  const [replyText, setReplyText] = useState("");
  const [submittingReply, setSubmittingReply] = useState(false);
  const [openRepliesId, setOpenRepliesId] = useState<number | null>(null);
  const [repliesCache, setRepliesCache] = useState<Record<number, ApiReply[]>>({});
  const [loadingReplies, setLoadingReplies] = useState(false);

  // Fetch comments for video when modal opens or content changes
  useEffect(() => {
    if (open && content?.id) {
      setLoadingVideoComments(true);
      getAdminComments({ videoId: content.id })
        .then((res) => setVideoComments(res.data))
        .catch((err) => console.warn("Failed to fetch comments for video:", err))
        .finally(() => setLoadingVideoComments(false));
    } else if (!open) {
      setVideoComments([]);
      setAdminCommentText("");
      setReplyOpenId(null);
      setReplyText("");
      setOpenRepliesId(null);
    }
  }, [open, content?.id]);

  const handlePostAdminComment = async () => {
    if (!adminCommentText.trim() || !content?.id) return;
    setPostingAdminComment(true);
    try {
      const created = await postAdminVideoComment(content.id, adminCommentText);
      setVideoComments((prev) => [created, ...prev]);
      setAdminCommentText("");
    } catch (err) {
      console.error("Failed to post admin comment:", err);
    } finally {
      setPostingAdminComment(false);
    }
  };

  const handleToggleLike = async (commentId: number) => {
    try {
      const res = await toggleCommentLike(commentId);
      setVideoComments((prev) =>
        prev.map((c) => (c.id === commentId ? { ...c, isLiked: res.isLiked, likes: res.likes } : c))
      );
    } catch (err) {
      console.error("Failed to toggle comment like:", err);
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!confirm("Are you sure you want to delete this comment?")) return;
    try {
      await apiDeleteComment(commentId);
      setVideoComments((prev) => prev.filter((c) => c.id !== commentId));
    } catch (err) {
      console.error("Failed to delete comment:", err);
    }
  };

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
        console.warn("Failed to load replies:", err);
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
      console.error("Failed to toggle reply like:", err);
    }
  };

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
      setVideoComments((prev) =>
        prev.map((c) => (c.id === parentCommentId ? { ...c, replyCount: c.replyCount + 1 } : c))
      );
      setOpenRepliesId(parentCommentId);
      setReplyText("");
      setReplyOpenId(null);
    } catch (err) {
      console.error("Failed to post reply:", err);
    } finally {
      setSubmittingReply(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
    };
  }, []);

  const handleToggleFullscreen = () => {
    if (!playerContainerRef.current) return;
    if (!document.fullscreenElement) {
      playerContainerRef.current.requestFullscreen().catch((err) => {
        console.warn("Fullscreen request failed:", err);
      });
    } else {
      document.exitFullscreen().catch((err) => {
        console.warn("Exit fullscreen failed:", err);
      });
    }
  };

  useEffect(() => {
    if (!open || !content) {
      fetchedVideoIdRef.current = null;
      setFetchedDetails(null);
      setFetchedUrl(null);
      setPlaybackError(false);
      setDynamicDuration(null);
      setDownloading(false);
      setDownloadProgress(null);
      setSelectedTrackUrl(null);
      setIsCcMenuOpen(false);
      setIsDownloadMenuOpen(false);
      return;
    }

    if (fetchedVideoIdRef.current === content.id) {
      return;
    }
    fetchedVideoIdRef.current = content.id;

    setPlaybackError(false);
    setDynamicDuration(null);
    setFetchedUrl(null);
    setVideoAspectRatio("16/9");
    setDownloading(false);
    setDownloadProgress(null);
    setSelectedTrackUrl(null);
    setIsCcMenuOpen(false);
    setIsDownloadMenuOpen(false);

    const existing = getOriginalVideoUrl(content);
    if (existing) {
      setFetchedUrl(existing);
    } else {
      setLoadingStream(true);
    }

    getVideoDetails(content.id)
      .then((res) => {
        setFetchedDetails(res);
        const url = res.playbackUrl || res.videoUrl || (res as any).playback_url || (res as any).video_url;
        if (url) {
          setFetchedUrl(url);
        } else if (!existing) {
          setPlaybackError(true);
          if (onPlaybackError) {
            onPlaybackError(`Something went wrong: Backend has not generated a stream URL for "${content.title}".`);
          }
        }
      })
      .catch((err) => {
        console.warn("Failed to fetch video details from backend API", err);
        if (!existing) {
          setPlaybackError(true);
          if (onPlaybackError) {
            onPlaybackError(`Something went wrong loading video asset from server for "${content.title}".`);
          }
        }
      })
      .finally(() => setLoadingStream(false));
  }, [content?.id, open]);

  const activeContent = useMemo(() => {
    if (!content) return null;
    if (!fetchedDetails) return content;
    return {
      ...content,
      description: fetchedDetails.description || (fetchedDetails as any).desc || content.description,
      captionsData: (fetchedDetails.captionsData && fetchedDetails.captionsData.length > 0) ? fetchedDetails.captionsData : content.captionsData,
      captionUrl: fetchedDetails.captionUrl || content.captionUrl,
      captionSrclang: fetchedDetails.captionSrclang || content.captionSrclang,
      captionLabel: fetchedDetails.captionLabel || content.captionLabel,
      downloadUrls: (fetchedDetails.downloadUrls && fetchedDetails.downloadUrls.length > 0) ? fetchedDetails.downloadUrls : content.downloadUrls,
      tags: (fetchedDetails.tags && fetchedDetails.tags.length > 0) ? fetchedDetails.tags : content.tags,
    };
  }, [content, fetchedDetails]);

  const availableCaptions = useMemo<CaptionTrack[]>(() => {
    const c = activeContent;
    if (!c) return [];
    const list: CaptionTrack[] = [];

    if (c.captionsData && c.captionsData.length > 0) {
      for (const item of c.captionsData) {
        if (item.url) {
          list.push({
            srclang: item.srclang || "en",
            label: item.label || (item.srclang ? item.srclang.toUpperCase() : "English"),
            url: item.url,
          });
        }
      }
    } else if (c.captionUrl) {
      list.push({
        srclang: c.captionSrclang || "en",
        label: c.captionLabel || "English",
        url: c.captionUrl,
      });
    }

    return list;
  }, [activeContent]);

  const handleVideoError = useCallback(() => {
    setPlaybackError(true);
    if (onPlaybackError && activeContent) {
      onPlaybackError(`Something went wrong loading video "${activeContent.title}". Media stream unreachable.`);
    }
  }, [onPlaybackError, activeContent?.title]);

  const handleLoadedMetadata = useCallback((e: React.SyntheticEvent<HTMLVideoElement, Event>) => {
    const video = e.currentTarget;
    const dur = video.duration;
    if (dur && !isNaN(dur) && isFinite(dur) && activeContent) {
      setDynamicDuration(formatDuration(dur, activeContent.id));
    }
    if (video.videoWidth && video.videoHeight) {
      setVideoAspectRatio(`${video.videoWidth} / ${video.videoHeight}`);
    }
  }, [activeContent?.id]);

  if (!content || !activeContent) return null;

  const videoSrc = fetchedUrl || getOriginalVideoUrl(activeContent);

  const handleDownload = async () => {
    if (!videoSrc || downloading) return;
    setDownloading(true);
    setDownloadProgress(0);

    const cleanTitle = (activeContent.title || "video").replace(/[^a-z0-9]/gi, "_");
    const filename = `${cleanTitle}.mp4`;

    try {
      let targetUrl = videoSrc;
      if (activeContent.downloadUrls && activeContent.downloadUrls.length > 0 && activeContent.downloadUrls[0].url) {
        targetUrl = activeContent.downloadUrls[0].url;
      } else if (targetUrl.includes(".m3u8")) {
        if (targetUrl.includes("playlist.m3u8")) {
          targetUrl = targetUrl.replace("playlist.m3u8", "play_720p.mp4");
        }
      }

      const res = await fetch(targetUrl);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const contentLength = res.headers.get("content-length");
      const totalBytes = contentLength ? parseInt(contentLength, 10) : 0;

      if (res.body && totalBytes > 0) {
        const reader = res.body.getReader();
        let loaded = 0;
        const chunks: BlobPart[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value) {
            chunks.push(value);
            loaded += value.length;
            setDownloadProgress(Math.round((loaded / totalBytes) * 100));
          }
        }

        const blob = new Blob(chunks, { type: "video/mp4" });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
      } else {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
      }
    } catch (err) {
      console.warn("Direct blob fetch download failed, triggering link download fallback:", err);
      const a = document.createElement("a");
      a.href = videoSrc;
      a.download = filename;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } finally {
      setDownloading(false);
      setDownloadProgress(null);
    }
  };

  const handleDownloadTarget = async (targetUrl: string, customFilename?: string) => {
    if (!targetUrl || downloading) return;
    setDownloading(true);
    setDownloadProgress(0);

    const cleanTitle = (activeContent.title || "video").replace(/[^a-z0-9]/gi, "_");
    const filename = customFilename || `${cleanTitle}.mp4`;

    try {
      const res = await fetch(targetUrl);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const contentLength = res.headers.get("content-length");
      const totalBytes = contentLength ? parseInt(contentLength, 10) : 0;

      if (res.body && totalBytes > 0) {
        const reader = res.body.getReader();
        let loaded = 0;
        const chunks: BlobPart[] = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          if (value) {
            chunks.push(value);
            loaded += value.length;
            setDownloadProgress(Math.round((loaded / totalBytes) * 100));
          }
        }

        const blob = new Blob(chunks, { type: "video/mp4" });
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
      } else {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
      }
    } catch (err) {
      console.warn("Direct blob fetch download failed, triggering link download fallback:", err);
      const a = document.createElement("a");
      a.href = targetUrl;
      a.download = filename;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    } finally {
      setDownloading(false);
      setDownloadProgress(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[85vh] flex flex-col p-0 overflow-hidden bg-slate-950 border border-slate-800 shadow-2xl text-white rounded-2xl [&>button:last-child]:hidden">
        {/* YouTube Studio Header Bar */}
        <div className="flex-shrink-0 flex items-center justify-between px-5 py-3 bg-slate-900 border-b border-slate-800">
          <div className="flex items-center gap-2.5 min-w-0 pr-4">
            <div className="h-7 w-7 rounded-lg bg-purple-950/80 border border-purple-800 flex items-center justify-center flex-shrink-0">
              <Video className="h-3.5 w-3.5 text-purple-400" />
            </div>
            <div className="min-w-0">
              <DialogTitle className="text-sm font-bold text-white truncate leading-tight">
                {activeContent.title}
              </DialogTitle>
              <DialogDescription className="text-[11px] text-slate-400 truncate">
                {activeContent.category || "Video Preview"} · {activeContent.date || "Video Details"}
              </DialogDescription>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            <button
              type="button"
              onClick={handleToggleFullscreen}
              className="h-7 w-7 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
              title={isFullscreen ? "Exit Fullscreen (Esc)" : "Fullscreen"}
            >
              {isFullscreen ? <Minimize2 className="h-3.5 w-3.5 text-purple-400" /> : <Maximize2 className="h-3.5 w-3.5" />}
            </button>

            <button
              type="button"
              onClick={onClose}
              className="h-7 w-7 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
              title="Close Preview (Esc)"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Player Container - Compact Screen Size */}
        <div ref={playerContainerRef} className="flex-shrink-0 relative w-full bg-black flex items-center justify-center overflow-hidden min-h-[180px] max-h-[35vh]" style={{ aspectRatio: videoAspectRatio }}>
          {loadingStream ? (
            <div className="flex flex-col items-center justify-center space-y-3 text-slate-400">
              <Loader2 className="h-8 w-8 animate-spin text-purple-500 text-xs font-medium" />
              <p className="text-xs font-medium">Fetching original stream URL from server...</p>
            </div>
          ) : playbackError || !videoSrc ? (
            <div className="flex flex-col items-center justify-center p-8 text-center bg-slate-900 border border-red-900/50 rounded-xl max-w-md mx-auto my-8 space-y-3">
              <div className="h-12 w-12 rounded-full bg-red-950/80 border border-red-800 flex items-center justify-center">
                <AlertCircle className="h-6 w-6 text-red-500" />
              </div>
              <div>
                <h3 className="font-bold text-lg text-white">Something went wrong</h3>
                <p className="text-sm text-slate-400 mt-1">Unable to play video asset. The original video URL is missing or media server is unreachable.</p>
              </div>
              <Button variant="outline" size="sm" className="bg-slate-800 hover:bg-slate-700 text-white border-slate-700 text-xs mt-2" onClick={() => setPlaybackError(false)}>
                <RefreshCw className="h-3.5 w-3.5 mr-1.5" /> Try Again
              </Button>
            </div>
          ) : (
            <HlsVideoPlayer
              key={activeContent.id}
              videoSrc={videoSrc}
              poster={activeContent.thumbnailUrl}
              captions={availableCaptions}
              selectedTrackUrl={selectedTrackUrl}
              onError={handleVideoError}
              onLoadedMetadata={handleLoadedMetadata}
            />
          )}
        </div>

        {/* Controls & Metadata Footer - Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-slate-900 border-t border-slate-800 custom-scrollbar">
          <div className="flex flex-col md:flex-row items-start justify-between gap-4">
            {/* Category & Tags on the left */}
            <div className="flex-1 space-y-2">
              <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider">
                {activeContent.category || "Uncategorized"}
              </h4>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1">Tags:</span>
                {activeContent.tags && activeContent.tags.length > 0 ? (
                  activeContent.tags.map((t) => (
                    <Badge
                      key={t}
                      variant="outline"
                      className="bg-purple-950/70 border-purple-800/60 text-purple-300 text-xs px-2.5 py-0.5 rounded-full"
                    >
                      #{t.replace(/^#/, "")}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-slate-500 italic">No tags attached</span>
                )}
              </div>
            </div>

            {/* Download MP4 Action on the right */}
            <div className="flex-shrink-0 pt-1">
              {activeContent.downloadUrls && activeContent.downloadUrls.length > 0 ? (
                <div className="relative">
                  <Button
                    onClick={() => setIsDownloadMenuOpen((prev) => !prev)}
                    disabled={!videoSrc || downloading}
                    className="gap-2 bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs px-3.5 h-9 rounded-xl shadow-lg cursor-pointer transition-all disabled:opacity-50"
                  >
                    {downloading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin text-purple-200" />
                        <span>{downloadProgress !== null ? `${downloadProgress}%` : "Downloading..."}</span>
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4" />
                        <span>Download MP4</span>
                        <ChevronDown className="h-3 w-3 opacity-70" />
                      </>
                    )}
                  </Button>

                  {isDownloadMenuOpen && (
                    <div className="absolute right-0 bottom-full mb-2 w-56 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl backdrop-blur-xl py-1 z-50 text-xs text-slate-200">
                      <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 border-b border-slate-800 flex items-center justify-between">
                        <span>Select MP4 Resolution</span>
                        <Download className="h-3 w-3 text-purple-400" />
                      </div>
                      {activeContent.downloadUrls.map((item) => (
                        <button
                          key={item.url}
                          type="button"
                          onClick={() => {
                            setIsDownloadMenuOpen(false);
                            const cleanTitle = (activeContent.title || "video").replace(/[^a-z0-9]/gi, "_");
                            handleDownloadTarget(item.url, `${cleanTitle}_${item.resolution || "hd"}.mp4`);
                          }}
                          className="w-full text-left px-3 py-2 flex items-center justify-between hover:bg-purple-950/50 hover:text-purple-300 transition-colors cursor-pointer"
                        >
                          <span className="font-medium text-slate-200">{item.label || item.resolution}</span>
                          <span className="text-[10px] font-mono text-purple-400 bg-purple-950 px-1.5 py-0.5 rounded border border-purple-800">
                            {item.resolution}
                          </span>
                        </button>
                      ))}
                      <div className="border-t border-slate-800 mt-1 pt-1">
                        <button
                          type="button"
                          onClick={() => {
                            setIsDownloadMenuOpen(false);
                            handleDownload();
                          }}
                          className="w-full text-left px-3 py-1.5 text-[11px] text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                        >
                          Default Stream URL
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <Button
                  onClick={handleDownload}
                  disabled={!videoSrc || downloading}
                  className="gap-2 bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs px-3.5 h-9 rounded-xl shadow-lg cursor-pointer transition-all disabled:opacity-50"
                >
                  {downloading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin text-purple-200" />
                      <span>{downloadProgress !== null ? `${downloadProgress}%` : "Downloading..."}</span>
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4" />
                      <span>Download Video</span>
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Total Views", value: activeContent.views || "0" },
              { label: "Duration", value: dynamicDuration || formatDuration(activeContent.duration, activeContent.id) },
              { label: "Access Tier", value: activeContent.premium ? "Premium" : "Free" },
            ].map((s) => (
              <div key={s.label} className="bg-slate-800/80 border border-slate-700/50 rounded-xl p-3 text-center">
                <div className="font-bold text-base text-white">{s.value}</div>
                <div className="text-xs text-slate-400">{s.label}</div>
              </div>
            ))}
          </div>

          {/* Description Section at the bottom with full width and smooth scrollability */}
          <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Description</h4>
            <div className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-3.5 text-sm text-slate-200 leading-relaxed whitespace-pre-line break-words min-h-[80px] max-h-[220px] overflow-y-auto custom-scrollbar">
              {activeContent.description || "No description available for this video content."}
            </div>
          </div>

          {/* Comments & Discussion Section for Admin */}
          <div className="pt-3 border-t border-slate-800/80 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-purple-400" />
                <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Comments & Discussion ({videoComments.length})
                </h4>
              </div>
              <span className="text-[11px] text-slate-500">Admin Comment Mode</span>
            </div>

            {/* Post Admin Comment Box */}
            <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3 space-y-2">
              <Textarea
                placeholder="Write an official creator comment on this video..."
                value={adminCommentText}
                onChange={(e) => setAdminCommentText(e.target.value)}
                className="bg-slate-900 border-slate-700/70 text-slate-200 text-xs focus:border-purple-500 min-h-[60px] resize-none"
              />
              <div className="flex items-center justify-between pt-1">
                <span className="text-[10px] text-slate-500 italic">Posted as Creator Admin</span>
                <Button
                  size="sm"
                  disabled={!adminCommentText.trim() || postingAdminComment}
                  onClick={handlePostAdminComment}
                  className="bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs h-8 px-3 rounded-lg gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {postingAdminComment ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>Posting...</span>
                    </>
                  ) : (
                    <>
                      <Send className="h-3.5 w-3.5" />
                      <span>Post Comment</span>
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Video Comments List */}
            <div className="space-y-2.5 max-h-[280px] overflow-y-auto custom-scrollbar pr-1">
              {loadingVideoComments ? (
                <div className="flex items-center justify-center py-6 text-slate-400 gap-2 text-xs">
                  <Loader2 className="h-4 w-4 animate-spin text-purple-500" /> Loading video comments...
                </div>
              ) : videoComments.length === 0 ? (
                <div className="text-center py-6 text-slate-500 text-xs bg-slate-950/40 rounded-xl border border-slate-800/60">
                  <MessageSquare className="h-6 w-6 mx-auto mb-1.5 opacity-30 text-purple-400" />
                  <p>No comments on this video yet.</p>
                  <p className="text-[11px] text-slate-600">Be the first to post a creator comment above.</p>
                </div>
              ) : (
                videoComments.map((comment) => (
                  <div key={comment.id} className="bg-slate-800/40 border border-slate-700/50 rounded-xl p-3 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="h-7 w-7 rounded-full bg-purple-950 border border-purple-800 flex items-center justify-center text-purple-300 font-bold text-xs overflow-hidden">
                          {comment.userAvatar ? (
                            <img src={comment.userAvatar} alt={comment.userName} className="w-full h-full object-cover" />
                          ) : (
                            comment.userName.charAt(0)
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                            <span>{comment.userName}</span>
                            <Badge className="bg-purple-950/80 border-purple-800 text-purple-300 text-[10px] px-1.5 py-0">
                              Creator
                            </Badge>
                          </div>
                          <div className="text-[10px] text-slate-500">
                            {new Date(comment.createdAt).toLocaleString()}
                          </div>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteComment(comment.id)}
                        className="h-6 w-6 text-slate-400 hover:text-red-400 cursor-pointer"
                        title="Delete comment"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>

                    <p className="text-slate-300 leading-relaxed ml-9 whitespace-pre-line">{comment.text}</p>

                    <div className="flex items-center justify-between ml-9 text-[11px] text-slate-400 pt-1">
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => handleToggleLike(comment.id)}
                          className={`flex items-center gap-1 transition-colors cursor-pointer ${comment.isLiked ? "text-purple-400 font-bold" : "hover:text-purple-300"}`}
                        >
                          <Heart className={`h-3.5 w-3.5 ${comment.isLiked ? "fill-purple-500 text-purple-500" : ""}`} />
                          {comment.likes}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleToggleReplies(comment.id)}
                          className="flex items-center gap-1 hover:text-purple-300 transition-colors cursor-pointer"
                        >
                          <MessageCircle className="h-3.5 w-3.5" />
                          {comment.replyCount}
                        </button>
                      </div>

                      <button
                        type="button"
                        onClick={() => {
                          setReplyOpenId(replyOpenId === comment.id ? null : comment.id);
                          setReplyText("");
                        }}
                        className="flex items-center gap-1 text-purple-400 hover:text-purple-300 font-medium cursor-pointer"
                      >
                        <CornerDownRight className="h-3 w-3" /> Reply
                      </button>
                    </div>

                    {/* Inline reply composer */}
                    {replyOpenId === comment.id && (
                      <div className="mt-2 ml-9 flex gap-2">
                        <Input
                          placeholder={`Reply to ${comment.userName}...`}
                          value={replyText}
                          onChange={(e) => setReplyText(e.target.value)}
                          className="bg-slate-900 border-slate-700 text-slate-200 h-8 text-xs"
                          autoFocus
                        />
                        <Button
                          size="sm"
                          disabled={!replyText.trim() || submittingReply}
                          onClick={() => handleSendReply(comment.id)}
                          className="bg-purple-600 hover:bg-purple-500 text-white h-8 px-2.5 cursor-pointer"
                        >
                          {submittingReply ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Send className="h-3.5 w-3.5" />}
                        </Button>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-400 cursor-pointer" onClick={() => { setReplyOpenId(null); setReplyText(""); }}>
                          <X className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}

                    {/* Replies Thread */}
                    {openRepliesId === comment.id && (
                      <div className="mt-2 ml-9 pt-2 border-t border-slate-700/50 space-y-1.5">
                        {loadingReplies ? (
                          <div className="flex items-center gap-1.5 text-[11px] text-slate-400 py-1">
                            <Loader2 className="h-3 w-3 animate-spin text-purple-400" /> Loading replies...
                          </div>
                        ) : (repliesCache[comment.id] || []).length === 0 ? (
                          <p className="text-[11px] text-slate-500 py-0.5 italic">No replies in this thread yet.</p>
                        ) : (
                          (repliesCache[comment.id] || []).map((reply) => {
                            const isSubReplyOpen = replyOpenId === `reply-${reply.id}`;
                            return (
                              <div key={reply.id} className="bg-slate-900/60 p-2 rounded-lg text-[11px] space-y-1 border border-slate-800/60">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-1.5">
                                    <span className="font-semibold text-purple-300 flex items-center gap-1">
                                      {reply.userName}
                                      {reply.isCreator && (
                                        <Badge className="bg-purple-950/80 border-purple-800 text-purple-300 text-[9px] px-1 py-0">
                                          Creator
                                        </Badge>
                                      )}
                                    </span>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <span className="text-[9px] text-slate-500">{new Date(reply.createdAt).toLocaleDateString()}</span>
                                  </div>
                                </div>

                                <p className="text-slate-300 whitespace-pre-line">{reply.text}</p>

                                {/* Subcomment stats and reply button bar */}
                                <div className="flex items-center justify-between pt-1 text-[10px] text-slate-400">
                                  <div className="flex items-center gap-3">
                                    <button
                                      type="button"
                                      onClick={() => handleToggleReplyLike(comment.id, reply.id)}
                                      className={`flex items-center gap-1 font-medium transition-colors cursor-pointer ${reply.isLiked ? "text-purple-400" : "hover:text-purple-400"}`}
                                    >
                                      <Heart className={`h-3 w-3 ${reply.isLiked ? "fill-purple-400 text-purple-400" : ""}`} />
                                      {reply.likes || 0}
                                    </button>
                                  </div>

                                  <button
                                    type="button"
                                    onClick={() => {
                                      if (isSubReplyOpen) {
                                        setReplyOpenId(null);
                                        setReplyText("");
                                      } else {
                                        setReplyOpenId(`reply-${reply.id}`);
                                        setReplyText(`@${reply.userName} `);
                                      }
                                    }}
                                    className="text-purple-400 hover:text-purple-300 font-medium flex items-center gap-0.5 cursor-pointer text-[10px]"
                                  >
                                    <CornerDownRight className="h-2.5 w-2.5" /> Reply
                                  </button>
                                </div>

                                {/* Inline sub-comment reply composer */}
                                {isSubReplyOpen && (
                                  <div className="mt-1.5 flex gap-1.5">
                                    <Input
                                      placeholder={`Reply to ${reply.userName}...`}
                                      value={replyText}
                                      onChange={(e) => setReplyText(e.target.value)}
                                      className="bg-slate-950 border-slate-700 text-slate-200 h-7 text-[11px]"
                                      autoFocus
                                    />
                                    <Button
                                      size="sm"
                                      disabled={!replyText.trim() || submittingReply}
                                      onClick={() => handleSendReply(comment.id, reply.id)}
                                      className="bg-purple-600 hover:bg-purple-500 text-white h-7 px-2 text-[11px] cursor-pointer"
                                    >
                                      {submittingReply ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-7 w-7 p-0 text-slate-400 cursor-pointer"
                                      onClick={() => { setReplyOpenId(null); setReplyText(""); }}
                                    >
                                      <X className="h-3 w-3" />
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
                ))
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── View content details dialog ────────────────────────────────────────────
function ViewContentDialog({ open, onClose, content, onPlay }: {
  open: boolean; onClose: () => void; content: Content | null; onPlay: (c: Content) => void;
}) {
  if (!content) return null;
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl">
        <DialogHeader>
          <DialogTitle>{content.title}</DialogTitle>
          <DialogDescription>Content details & metadata</DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div
            className="relative h-48 w-full rounded-xl bg-slate-950 flex items-center justify-center overflow-hidden cursor-pointer group"
            onClick={() => { onClose(); onPlay(content); }}
          >
            {content.thumbnailUrl ? (
              <img src={content.thumbnailUrl} alt={content.title} className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
            ) : (
              <Video className="h-16 w-16 text-purple-400 opacity-50" />
            )}
            <div className="absolute inset-0 flex items-center justify-center bg-black/30 group-hover:bg-black/40 transition-colors">
              <div className="h-14 w-14 rounded-full bg-white/90 flex items-center justify-center shadow-2xl group-hover:scale-110 transition-transform">
                <Play className="h-7 w-7 text-purple-700 ml-1" />
              </div>
            </div>
            <div className="absolute top-3 left-3">
              <Badge variant={content.status === "Published" ? "default" : content.status === "Draft" ? "secondary" : "outline"}>{content.status}</Badge>
            </div>
            <div className="absolute bottom-3 right-3 bg-black/80 text-white text-xs px-2 py-0.5 rounded">{content.duration}</div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Views", value: content.views || "0" },
              { label: "Category", value: content.category },
              { label: "Date Added", value: content.date },
            ].map((s) => (
              <div key={s.label} className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
                <div className="font-bold text-sm text-slate-800">{s.value}</div>
                <div className="text-xs text-slate-500">{s.label}</div>
              </div>
            ))}
          </div>
          <div>
            <Label className="text-xs text-slate-400 uppercase tracking-wide">Description</Label>
            <p className="mt-1 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{content.description || "No description provided."}</p>
          </div>

          {/* Subtitles & Captions info */}
          {content.captionsData && content.captionsData.length > 0 && (
            <div>
              <Label className="text-xs text-slate-400 uppercase tracking-wide flex items-center gap-1 mb-1.5">
                <Subtitles className="h-3.5 w-3.5 text-purple-400" /> Subtitles ({content.captionsData.length})
              </Label>
              <div className="flex flex-wrap gap-1.5">
                {content.captionsData.map((c, i) => (
                  <Badge key={i} variant="outline" className="bg-purple-950/40 border-purple-800 text-purple-300 text-xs">
                    {c.label || c.srclang || "Subtitles"}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Download URLs info */}
          {content.downloadUrls && content.downloadUrls.length > 0 && (
            <div>
              <Label className="text-xs text-slate-400 uppercase tracking-wide flex items-center gap-1 mb-1.5">
                <Download className="h-3.5 w-3.5 text-emerald-400" /> Download Qualities ({content.downloadUrls.length})
              </Label>
              <div className="flex flex-wrap gap-1.5">
                {content.downloadUrls.map((dl, i) => (
                  <a
                    key={i}
                    href={dl.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 bg-emerald-950/40 border border-emerald-800 text-emerald-300 hover:text-white text-xs px-2.5 py-1 rounded-md transition-colors"
                  >
                    <Download className="h-3 w-3" />
                    <span>{dl.label || dl.resolution}</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {content.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {content.tags.map((t) => <span key={t} className="bg-purple-100 dark:bg-purple-950/80 text-purple-700 dark:text-purple-300 text-xs px-2.5 py-0.5 rounded-full">#{t}</span>)}
            </div>
          )}
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>Close</Button>
          <Button onClick={() => { onClose(); onPlay(content); }} className="gap-2 bg-slate-900 text-white hover:bg-slate-800">
            <Play className="h-4 w-4 fill-white" />Play Video
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ── Playlist Detail Screen (YouTube Studio Style) ───────────────────────────
function PlaylistDetailScreen({
  playlist, playlists, allVideos, onBack, onEditMeta, onRefresh,
}: {
  playlist: Playlist;
  playlists: Playlist[];
  allVideos: Content[];
  onBack: () => void;
  onEditMeta: (pl: Playlist) => void;
  onRefresh: () => void;
}) {
  const [currentPlaylist, setCurrentPlaylist] = useState<Playlist>(playlist);
  const [playlistVideos, setPlaylistVideos] = useState<Content[]>([]);
  const [loadingVideos, setLoadingVideos] = useState(true);
  const [selected, setSelected] = useState<number[]>([]);
  const [addVideosOpen, setAddVideosOpen] = useState(false);
  const [editVideoContent, setEditVideoContent] = useState<Content | null>(null);
  const [playingVideo, setPlayingVideo] = useState<Content | null>(null);
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const [currentThumbnail, setCurrentThumbnail] = useState<string | undefined>(playlist.thumbnailUrl);
  const bannerInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setCurrentPlaylist(playlist);
    setCurrentThumbnail(playlist.thumbnailUrl);
  }, [playlist]);

  const fetchPlaylistDetails = useCallback(async () => {
    try {
      const detailsRes = await getPlaylistDetails(playlist.id);
      if (detailsRes) {
        setCurrentPlaylist((prev) => ({
          ...prev,
          title: detailsRes.title || prev.title,
          description: detailsRes.description || (detailsRes as any).desc || (detailsRes as any).summary || (detailsRes as any).details || prev.description,
          thumbnailUrl: detailsRes.thumbnailUrl || prev.thumbnailUrl,
          videoIds: detailsRes.videoIds && detailsRes.videoIds.length > 0 ? detailsRes.videoIds : prev.videoIds,
        }));
        if (detailsRes.thumbnailUrl) {
          setCurrentThumbnail(detailsRes.thumbnailUrl);
        }
      }
    } catch (err) {
      console.warn("Failed to fetch details for playlist screen:", err);
    }
  }, [playlist.id]);

  useEffect(() => {
    fetchPlaylistDetails();
  }, [fetchPlaylistDetails]);

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadingBanner(true);
      try {
        const res = await uploadPlaylistBanner(playlist.id, file);
        if (res && (res as any).thumbnailUrl) {
          setCurrentThumbnail((res as any).thumbnailUrl);
        } else if (res && (res as any).bannerUrl) {
          setCurrentThumbnail((res as any).bannerUrl);
        } else {
          setCurrentThumbnail(URL.createObjectURL(file));
        }
        onRefresh();
      } catch (err) {
        console.error("Failed to upload playlist banner/thumbnail:", err);
      } finally {
        setUploadingBanner(false);
      }
    }
  };

  const fetchVideos = useCallback(async () => {
    setLoadingVideos(true);
    try {
      const res = await getPlaylistVideos(playlist.id);
      if (res?.data && Array.isArray(res.data) && res.data.length > 0) {
        const mapped: Content[] = res.data.map((item: ApiVideo) => ({
          id: item.id,
          title: item.title,
          type: "Video",
          category: item.category || "Uncategorized",
          status: item.status ? item.status.charAt(0).toUpperCase() + item.status.slice(1) : "Draft",
          views: item.views !== undefined ? item.views.toString() : "0",
          duration: item.duration || "0:00",
          date: item.date || new Date().toISOString().split("T")[0],
          premium: !!item.premium,
          description: item.description || "",
          tags: item.tags || [],
          thumbnailUrl: item.thumbnailUrl,
          captionsData: item.captionsData,
          captionUrl: item.captionUrl,
          captionSrclang: item.captionSrclang,
          captionLabel: item.captionLabel,
          downloadUrls: item.downloadUrls,
        }));
        setPlaylistVideos(mapped);
      } else {
        const fallback = allVideos.filter((c) => (playlist.videoIds || []).includes(c.id));
        setPlaylistVideos(fallback);
      }
    } catch (err) {
      console.warn("Failed to fetch playlist videos from API", err);
      const fallback = allVideos.filter((c) => (playlist.videoIds || []).includes(c.id));
      setPlaylistVideos(fallback);
    } finally {
      setLoadingVideos(false);
    }
  }, [playlist.id, playlist.videoIds, allVideos]);

  useEffect(() => {
    fetchVideos();
  }, [fetchVideos]);

  const videos = playlistVideos;
  const currentVideoIds = videos.map((v) => v.id);
  const totalViews = videos.reduce((acc, v) => acc + (parseInt(v.views, 10) || 0), 0);

  const toggleSelect = (id: number) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);

  const toggleAll = () =>
    setSelected(selected.length === videos.length ? [] : videos.map((v) => v.id));

  const removeSelected = async () => {
    try {
      await bulkRemoveVideosFromPlaylist(playlist.id, selected);
      setSelected([]);
      fetchVideos();
      onRefresh();
    } catch (err) {
      console.error("Failed to remove videos from playlist:", err);
    }
  };

  const removeSingle = async (id: number) => {
    try {
      await removeVideoFromPlaylist(playlist.id, id);
      setSelected((prev) => prev.filter((x) => x !== id));
      fetchVideos();
      onRefresh();
    } catch (err) {
      console.error("Failed to remove video from playlist:", err);
    }
  };

  const handleAdd = async (ids: number[]) => {
    try {
      await addVideosToPlaylist(playlist.id, ids);
      fetchVideos();
      onRefresh();
    } catch (err) {
      console.error("Failed to add videos to playlist:", err);
    }
  };

  return (
    <div className="space-y-6">
      <AddVideosDialog
        open={addVideosOpen}
        onClose={() => setAddVideosOpen(false)}
        excludeIds={currentVideoIds}
        allVideos={allVideos}
        playlistId={playlist.id}
        onAdd={handleAdd}
      />
      <EditVideoDialog
        open={!!editVideoContent}
        onClose={() => setEditVideoContent(null)}
        content={editVideoContent}
        playlists={playlists}
        onSaveSuccess={onRefresh}
      />
      <VideoPlayerDialog
        open={!!playingVideo}
        onClose={() => setPlayingVideo(null)}
        content={playingVideo}
      />

      <input
        type="file"
        ref={bannerInputRef}
        onChange={handleBannerUpload}
        accept="image/*"
        className="hidden"
      />

      {/* Back button header */}
      <div>
        <button
          onClick={onBack}
          className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-purple-400 transition-colors mb-2 group cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4 group-hover:-translate-x-1 transition-transform" /> Back to Playlists
        </button>
      </div>

      {/* ── YouTube-Style Playlist Hero Card at Top ── */}
      <div className="relative rounded-2xl bg-gradient-to-br from-slate-900/90 via-slate-900/80 to-slate-950/90 border border-slate-800/80 shadow-2xl backdrop-blur-xl p-6 md:p-8 overflow-hidden">
        {/* Background ambient glow */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row gap-6 md:gap-8 items-start relative z-10">
          {/* Playlist Thumbnail Container */}
          <div className="relative group w-full md:w-72 h-44 rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden shadow-2xl flex-shrink-0 flex items-center justify-center">
            {currentThumbnail ? (
              <img src={currentThumbnail} alt={playlist.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
            ) : (
              <div className="flex flex-col items-center justify-center space-y-2 text-slate-500">
                <ListVideo className="h-12 w-12 text-purple-400/60" />
                <span className="text-xs font-medium text-slate-400">No Playlist Thumbnail</span>
              </div>
            )}

            {/* Video count badge */}
            <div className="absolute bottom-2.5 right-2.5 bg-black/85 backdrop-blur-md text-white text-xs font-bold px-2.5 py-1 rounded-lg flex items-center gap-1.5 border border-white/10 shadow-lg">
              <ListVideo className="h-3.5 w-3.5 text-purple-400" />
              <span>{videos.length} {videos.length === 1 ? "Video" : "Videos"}</span>
            </div>

            {/* Overlay Edit Thumbnail Trigger */}
            <button
              onClick={() => bannerInputRef.current?.click()}
              disabled={uploadingBanner}
              className="absolute inset-0 bg-slate-950/80 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-white gap-2 font-semibold text-xs backdrop-blur-xs cursor-pointer"
            >
              {uploadingBanner ? (
                <>
                  <Loader2 className="h-7 w-7 animate-spin text-purple-400" />
                  <span>Uploading Thumbnail...</span>
                </>
              ) : (
                <>
                  <div className="h-10 w-10 rounded-full bg-purple-600/90 flex items-center justify-center shadow-lg">
                    <ImagePlus className="h-5 w-5 text-white" />
                  </div>
                  <span>Change Playlist Thumbnail</span>
                </>
              )}
            </button>
          </div>

          {/* Playlist Info & Metadata */}
          <div className="flex-1 min-w-0 flex flex-col justify-between self-stretch space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-purple-400 bg-purple-950/80 border border-purple-800/60 px-3 py-0.5 rounded-full">
                  <ListVideo className="h-3 w-3" /> Playlist Collection
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-100 tracking-tight leading-tight">
                {currentPlaylist.title}
              </h1>
              <p className="text-sm text-slate-300 leading-relaxed max-w-3xl line-clamp-3">
                {currentPlaylist.description || "No description provided for this playlist."}
              </p>
            </div>

            <div className="space-y-4 pt-2 border-t border-slate-800/80">
              <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-slate-400">
                <span className="text-slate-200 font-semibold">{videos.length} video{videos.length !== 1 ? "s" : ""}</span>
                <span className="text-slate-600">•</span>
                <span>Created {playlist.date}</span>
                <span className="text-slate-600">•</span>
                <span>{totalViews.toLocaleString()} total views</span>
              </div>

              {/* Action Toolbar */}
              <div className="flex flex-wrap items-center gap-2.5">
                {videos.length > 0 && (
                  <Button
                    className="gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold shadow-lg shadow-purple-950/50 border border-purple-500/30 h-9 px-4 cursor-pointer"
                    onClick={() => setPlayingVideo(videos[0])}
                  >
                    <Play className="h-4 w-4 fill-white" /> Play All
                  </Button>
                )}

                <Button
                  className="gap-2 bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700/80 font-medium h-9 px-3.5 text-xs cursor-pointer"
                  onClick={() => setAddVideosOpen(true)}
                >
                  <Plus className="h-4 w-4 text-purple-400" /> Add Videos
                </Button>

                <Button
                  variant="outline"
                  className="gap-2 border-slate-800 bg-slate-950/80 hover:bg-slate-800 text-slate-200 h-9 px-3.5 text-xs cursor-pointer"
                  onClick={() => bannerInputRef.current?.click()}
                  disabled={uploadingBanner}
                >
                  {uploadingBanner ? (
                    <Loader2 className="h-4 w-4 animate-spin text-purple-400" />
                  ) : (
                    <ImagePlus className="h-4 w-4 text-purple-400" />
                  )}
                  Edit Thumbnail
                </Button>

                <Button
                  variant="outline"
                  className="gap-2 border-slate-800 bg-slate-950/80 hover:bg-slate-800 text-slate-200 h-9 px-3.5 text-xs cursor-pointer"
                  onClick={() => onEditMeta(currentPlaylist)}
                >
                  <Pencil className="h-4 w-4 text-slate-400" /> Edit Details
                </Button>

                {selected.length > 0 && (
                  <Button
                    variant="destructive"
                    className="gap-2 font-medium h-9 px-3.5 text-xs ml-auto cursor-pointer"
                    onClick={removeSelected}
                  >
                    <Trash2 className="h-4 w-4" /> Remove Selected ({selected.length})
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Selection Action Bar ── */}
      {selected.length > 0 && (
        <div className="flex items-center justify-between bg-purple-950/80 border border-purple-800/60 rounded-xl px-5 py-3 shadow-lg backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <CheckSquare className="h-5 w-5 text-purple-400" />
            <span className="text-sm font-semibold text-purple-200">
              {selected.length} video{selected.length > 1 ? "s" : ""} selected
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white text-xs cursor-pointer" onClick={() => setSelected([])}>
              Deselect All
            </Button>
            <Button variant="destructive" size="sm" className="gap-1.5 text-xs cursor-pointer" onClick={removeSelected}>
              <Trash2 className="h-3.5 w-3.5" /> Remove from Playlist
            </Button>
          </div>
        </div>
      )}

      {/* ── YouTube-Style Playlist Video List (Bottom Section) ── */}
      <Card className="border border-slate-800/80 bg-slate-900/60 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
        {/* List Header */}
        <div className="bg-slate-950/80 border-b border-slate-800/80 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              className="h-4 w-4 rounded accent-purple-600 cursor-pointer"
              checked={selected.length === videos.length && videos.length > 0}
              onChange={toggleAll}
            />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Playlist Videos ({videos.length})
            </span>
          </div>
          <span className="text-xs text-slate-500 font-medium">Click any item to play</span>
        </div>

        <CardContent className="p-0">
          {loadingVideos ? (
            <div className="flex items-center justify-center py-20 text-slate-400 gap-3">
              <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
              <span className="font-medium text-sm">Loading playlist videos...</span>
            </div>
          ) : videos.length === 0 ? (
            <div className="text-center py-20 text-slate-500">
              <ListVideo className="h-12 w-12 mx-auto mb-3 opacity-40 text-purple-400" />
              <p className="font-semibold text-slate-300">No videos in this playlist yet</p>
              <p className="text-xs text-slate-500 mt-1">Add videos to build your playlist collection</p>
              <Button className="mt-4 gap-2 bg-purple-600 hover:bg-purple-500 text-white cursor-pointer" onClick={() => setAddVideosOpen(true)}>
                <Plus className="h-4 w-4" /> Add Videos Now
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60">
              {videos.map((v, index) => (
                <div
                  key={v.id}
                  className="p-4 md:p-5 flex items-center gap-4 md:gap-6 hover:bg-slate-800/40 transition-colors group relative cursor-pointer"
                  onMouseEnter={() => setHoveredId(v.id)}
                  onMouseLeave={() => setHoveredId(null)}
                >
                  {/* Select Checkbox */}
                  <div onClick={(e) => e.stopPropagation()} className="flex-shrink-0">
                    <input
                      type="checkbox"
                      className="h-4 w-4 rounded accent-purple-600 cursor-pointer"
                      checked={selected.includes(v.id)}
                      onChange={() => toggleSelect(v.id)}
                    />
                  </div>

                  {/* Item Order Index Number */}
                  <span className="w-6 text-center text-xs font-mono font-bold text-slate-500 group-hover:text-purple-400 flex-shrink-0">
                    #{index + 1}
                  </span>

                  {/* YouTube Thumbnail Format */}
                  <div
                    className="relative h-20 w-36 rounded-xl bg-slate-950 flex-shrink-0 overflow-hidden border border-slate-800 shadow-md group-hover:border-purple-500/50 transition-all"
                    onClick={() => setPlayingVideo(v)}
                  >
                    {v.thumbnailUrl ? (
                      <img src={v.thumbnailUrl} alt={v.title} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Video className="h-6 w-6 text-purple-400 opacity-60" />
                      </div>
                    )}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                      <div className="h-9 w-9 rounded-full bg-purple-600/90 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all transform scale-90 group-hover:scale-100 shadow-lg">
                        <Play className="h-4 w-4 fill-white ml-0.5" />
                      </div>
                    </div>
                    <span className="absolute bottom-1 right-1 bg-black/85 text-white text-[10px] px-1.5 py-0.5 rounded font-mono font-medium">
                      {v.duration}
                    </span>
                  </div>

                  {/* Video Title & Metadata Information */}
                  <div className="flex-1 min-w-0 space-y-1" onClick={() => setPlayingVideo(v)}>
                    <div className="font-bold text-slate-100 text-base group-hover:text-purple-400 transition-colors truncate">
                      {v.title}
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400 font-medium">
                      <span>{v.category}</span>
                      <span className="text-slate-600">•</span>
                      <span>Added {v.date}</span>
                      <span className="text-slate-600">•</span>
                      <span>{v.views || "0"} views</span>
                    </div>
                    <div className="flex items-center gap-2 pt-1">
                      <Badge
                        variant="outline"
                        className={`text-[10px] font-mono ${v.status === "Published" || v.status === "published"
                          ? "bg-emerald-950/80 border-emerald-800/60 text-emerald-400"
                          : v.status === "Draft" || v.status === "draft"
                            ? "bg-slate-800 border-slate-700 text-slate-300"
                            : "bg-amber-950/80 border-amber-800/60 text-amber-400"
                          }`}
                      >
                        {v.status}
                      </Badge>
                      {v.premium && (
                        <Badge variant="outline" className="text-[10px] bg-purple-950/80 border-purple-800/60 text-purple-300">
                          Premium
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Action Buttons (Play, Edit Details, Remove) */}
                  <div className="flex items-center gap-1 flex-shrink-0" onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-slate-400 hover:text-purple-400 hover:bg-slate-800 cursor-pointer"
                      onClick={() => setPlayingVideo(v)}
                      title="Play Video"
                    >
                      <Play className="h-4 w-4 fill-current" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                      onClick={() => setEditVideoContent(v)}
                      title="Edit Video Details"
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-slate-400 hover:text-rose-400 hover:bg-rose-950/40 cursor-pointer"
                      onClick={() => removeSingle(v.id)}
                      title="Remove from Playlist"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}


// ── Main page ──────────────────────────────────────────────────────────────
export default function ContentManagement() {
  const [contents, setContents] = useState<Content[]>([]);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);

  // Navigation & Filter states
  const [activeTab, setActiveTab] = useState("videos");
  const [activePlaylist, setActivePlaylist] = useState<Playlist | null>(null);
  const [search, setSearch] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterDateFrom, setFilterDateFrom] = useState("");
  const [filterDateTo, setFilterDateTo] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [dateRangeOpen, setDateRangeOpen] = useState(false);
  const [playlistSearch, setPlaylistSearch] = useState("");
  const [playlistSortBy, setPlaylistSortBy] = useState("newest");

  // Dialog states
  const [uploadOpen, setUploadOpen] = useState(false);
  const [viewContent, setViewContent] = useState<Content | null>(null);
  const [editContent, setEditContent] = useState<Content | null>(null);
  const [playingVideo, setPlayingVideo] = useState<Content | null>(null);
  const [newPlaylistOpen, setNewPlaylistOpen] = useState(false);
  const [editPlaylistMeta, setEditPlaylistMeta] = useState<Playlist | null>(null);

  // Notification Toast state
  const [toast, setToast] = useState<{ show: boolean; title: string; message: string }>({ show: false, title: "", message: "" });
  const showToast = useCallback((title: string, message: string) => {
    setToast({ show: true, title, message });
    setTimeout(() => setToast((prev) => ({ ...prev, show: false })), 5000);
  }, []);

  const loadData = useCallback(async (isSilent = false) => {
    if (!isSilent) setLoading(true);
    try {
      const vRes = await getVideos({
        status: filterStatus !== "all" ? filterStatus.toLowerCase() : undefined,
        category: filterCategory !== "all" ? filterCategory : undefined,
        search: search.trim() || undefined,
        sort: sortBy,
        dateFrom: filterDateFrom || undefined,
        dateTo: filterDateTo || undefined,
      });

      if (vRes?.data && Array.isArray(vRes.data)) {
        const mapped: Content[] = vRes.data.map((item: ApiVideo) => ({
          id: item.id,
          title: item.title,
          type: "Video",
          category: item.category || "Uncategorized",
          status: item.status ? item.status.charAt(0).toUpperCase() + item.status.slice(1) : "Draft",
          views: item.views !== undefined ? item.views.toString() : "0",
          duration: item.duration || "0:00",
          date: item.date || new Date().toISOString().split("T")[0],
          premium: !!item.premium,
          description: item.description || "",
          tags: item.tags || [],
          thumbnailUrl: item.thumbnailUrl,
          encodeProgress: item.encodeProgress,
          captionsData: item.captionsData,
          captionUrl: item.captionUrl,
          captionSrclang: item.captionSrclang,
          captionLabel: item.captionLabel,
          downloadUrls: item.downloadUrls,
        }));
        setContents(mapped);
      }

      const pRes = await getPlaylists({
        search: playlistSearch.trim() || undefined,
        sort: playlistSortBy,
      });

      if (pRes?.data && Array.isArray(pRes.data)) {
        const mappedPl: Playlist[] = pRes.data.map((item: ApiPlaylist) => ({
          id: item.id,
          title: item.title,
          description: item.description || (item as any).desc || (item as any).summary || (item as any).details || "",
          videos: item.videoCount ?? (item.videoIds ? item.videoIds.length : 0),
          videoIds: item.videoIds || [],
          date: item.date || new Date().toISOString().split("T")[0],
          thumbnailUrl: item.thumbnailUrl,
        }));
        setPlaylists(mappedPl);
        if (activePlaylist) {
          const updated = mappedPl.find((p) => p.id === activePlaylist.id);
          if (updated) {
            setActivePlaylist(updated);
          }
        }
      }
    } catch (err) {
      console.warn("Failed to fetch data from backend API", err);
    } finally {
      if (!isSilent) setLoading(false);
    }
  }, [filterStatus, filterCategory, search, sortBy, filterDateFrom, filterDateTo, playlistSearch, playlistSortBy]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Real-time status polling for transcoding assets (silent background refresh)
  useEffect(() => {
    const hasTranscoding = contents.some((c) => {
      const s = (c.status || "").toLowerCase();
      return (
        (c.encodeProgress !== undefined && c.encodeProgress < 100) ||
        ["pending", "processing", "encoding", "uploading"].includes(s)
      );
    });

    if (hasTranscoding) {
      const timer = setInterval(() => {
        loadData(true);
      }, 5000);
      return () => clearInterval(timer);
    }
  }, [contents, loadData]);

  // Synchronize activePlaylist details when playlists list refreshes
  useEffect(() => {
    if (activePlaylist && playlists.length > 0) {
      const updated = playlists.find((p) => p.id === activePlaylist.id);
      if (updated) {
        setActivePlaylist((prev) => (prev ? { ...prev, ...updated } : updated));
      }
    }
  }, [playlists]);

  const handleDeleteVideo = async (id: number) => {
    try {
      await deleteVideo(id);
      loadData();
    } catch (err) {
      console.error("Failed to delete video:", err);
    }
  };

  const handleDeletePlaylist = async (id: number) => {
    try {
      await deletePlaylist(id);
      if (activePlaylist?.id === id) {
        setActivePlaylist(null);
      }
      loadData();
    } catch (err) {
      console.error("Failed to delete playlist:", err);
    }
  };

  const uniqueCategories = Array.from(new Set(contents.map((c) => c.category))).filter(Boolean);

  const activeCount =
    [filterStatus, filterCategory].filter((v) => v !== "all").length +
    (filterDateFrom ? 1 : 0);

  const resetFilters = () => {
    setFilterStatus("all");
    setFilterCategory("all");
    setFilterDateFrom("");
    setFilterDateTo("");
    setSortBy("newest");
    setSearch("");
  };

  const dateLabel = filterDateFrom
    ? filterDateTo && filterDateTo !== filterDateFrom
      ? `${filterDateFrom} → ${filterDateTo}`
      : filterDateFrom
    : null;

  // ── If viewing a playlist detail, render that screen ─────────────────────
  if (activePlaylist) {
    return (
      <div className="space-y-6">
        <PlaylistMetaDialog
          open={!!editPlaylistMeta}
          onClose={() => setEditPlaylistMeta(null)}
          playlist={editPlaylistMeta ?? undefined}
          allVideos={contents}
          onSaveSuccess={loadData}
        />
        <PlaylistDetailScreen
          playlist={activePlaylist}
          playlists={playlists}
          allVideos={contents}
          onBack={() => setActivePlaylist(null)}
          onEditMeta={(pl) => setEditPlaylistMeta(pl)}
          onRefresh={loadData}
        />
      </div>
    );
  }

  // ── Main view ────────────────────────────────────────────────────────────
  return (
    <div className="space-y-6">
      <UploadEditDialog open={uploadOpen} onClose={() => setUploadOpen(false)} playlists={playlists} onSaveSuccess={loadData} />
      <EditVideoDialog open={!!editContent} onClose={() => setEditContent(null)} content={editContent} playlists={playlists} onSaveSuccess={loadData} />
      <ViewContentDialog open={!!viewContent} onClose={() => setViewContent(null)} content={viewContent} onPlay={(c) => setPlayingVideo(c)} />
      <VideoPlayerDialog open={!!playingVideo} onClose={() => setPlayingVideo(null)} content={playingVideo} onPlaybackError={(msg) => showToast("Something went wrong", msg)} />
      <PlaylistMetaDialog open={newPlaylistOpen} onClose={() => setNewPlaylistOpen(false)} allVideos={contents} onSaveSuccess={loadData} />
      <PlaylistMetaDialog open={!!editPlaylistMeta} onClose={() => setEditPlaylistMeta(null)} playlist={editPlaylistMeta ?? undefined} allVideos={contents} onSaveSuccess={loadData} />
      <DateRangeDialog
        open={dateRangeOpen}
        onClose={() => setDateRangeOpen(false)}
        from={filterDateFrom}
        to={filterDateTo}
        onChange={(f, t) => { setFilterDateFrom(f); setFilterDateTo(t); }}
      />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Content Management</h1>
          <p className="text-slate-300 mt-1 text-sm font-medium">Upload, organize, and manage your OTT video library</p>
        </div>
        <div className="flex items-center gap-3">
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="icon" onClick={() => loadData()} title="Refresh Data" className="h-10 w-10 border-slate-800 bg-slate-900/80 hover:bg-slate-800 text-slate-300">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin text-purple-400" : ""}`} />
          </Button>
          {activeTab === "videos" && (
            <Button className="gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white h-10 px-4 font-semibold shadow-lg shadow-purple-950/50 border border-purple-500/30" onClick={() => setUploadOpen(true)}>
              <Plus className="h-4 w-4" />Upload Content
            </Button>
          )}
          {activeTab === "playlists" && (
            <Button className="gap-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white h-10 px-4 font-semibold shadow-lg shadow-purple-950/50 border border-purple-500/30" onClick={() => setNewPlaylistOpen(true)}>
              <Plus className="h-4 w-4" />New Playlist
            </Button>
          )}
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        {/* Dark Studio tab switcher */}
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
          <TabsList className="bg-slate-950/80 p-1.5 rounded-2xl border border-slate-800/80 backdrop-blur-xl">
            <TabsTrigger
              value="videos"
              className="gap-2 px-6 py-2.5 rounded-xl font-semibold transition-all data-[state=active]:bg-purple-600/90 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:shadow-purple-950/50 text-slate-400 hover:text-slate-200"
            >
              <Video className="h-4 w-4" />Videos
              <span className={`ml-1 text-xs px-2 py-0.5 rounded-full font-bold ${activeTab === "videos" ? "bg-white/20 text-white" : "bg-slate-800 text-slate-400"}`}>
                {contents.length}
              </span>
            </TabsTrigger>
            <TabsTrigger
              value="playlists"
              className="gap-2 px-6 py-2.5 rounded-xl font-semibold transition-all data-[state=active]:bg-purple-600/90 data-[state=active]:text-white data-[state=active]:shadow-lg data-[state=active]:shadow-purple-950/50 text-slate-400 hover:text-slate-200"
            >
              <ListVideo className="h-4 w-4" />Playlists
              <span className={`ml-1 text-xs px-2 py-0.5 rounded-full font-bold ${activeTab === "playlists" ? "bg-white/20 text-white" : "bg-slate-800 text-slate-400"}`}>
                {playlists.length}
              </span>
            </TabsTrigger>
          </TabsList>

          {activeTab === "videos" && (
            <div className="flex items-center gap-2.5">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input type="search" placeholder="Search videos..." className="pl-9 w-64 bg-slate-950/90 border-slate-800 text-slate-100 placeholder:text-slate-500"
                  value={search} onChange={(e) => setSearch(e.target.value)} />
              </div>
              <Button variant={showFilters ? "default" : "outline"} className={`gap-2 border-slate-800 ${showFilters ? "bg-purple-600 text-white hover:bg-purple-500" : "bg-slate-900 text-slate-300 hover:bg-slate-800"}`}
                onClick={() => setShowFilters(!showFilters)}>
                <SlidersHorizontal className="h-4 w-4" />Filters
                {activeCount > 0 && <span className="ml-1 bg-white/20 text-white rounded-full text-xs font-bold px-1.5">{activeCount}</span>}
              </Button>
            </div>
          )}

          {activeTab === "playlists" && (
            <div className="flex items-center gap-2.5">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input type="search" placeholder="Search playlists..." className="pl-9 w-64 bg-slate-950/90 border-slate-800 text-slate-100 placeholder:text-slate-500"
                  value={playlistSearch} onChange={(e) => setPlaylistSearch(e.target.value)} />
              </div>
              <Select value={playlistSortBy} onValueChange={setPlaylistSortBy}>
                <SelectTrigger className="h-10 text-sm w-40 bg-slate-950/90 border-slate-800 text-slate-100"><SelectValue /></SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                  <SelectItem value="newest">Newest first</SelectItem>
                  <SelectItem value="oldest">Oldest first</SelectItem>
                  <SelectItem value="title">Title A–Z</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* ── Videos Tab ── */}
        <TabsContent value="videos">
          <Card className="border border-slate-800/80 bg-slate-900/60 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
            {showFilters && (
              <CardHeader className="bg-slate-950/80 border-b border-slate-800/80 p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
                  <div>
                    <Label className="text-xs mb-1.5 block font-semibold text-slate-400 uppercase tracking-wider">Status</Label>
                    <Select value={filterStatus} onValueChange={setFilterStatus}>
                      <SelectTrigger className="h-9 text-sm bg-slate-900 border-slate-800 text-slate-100"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                        <SelectItem value="all">All Status</SelectItem>
                        <SelectItem value="Published">Published</SelectItem>
                        <SelectItem value="Draft">Draft</SelectItem>
                        <SelectItem value="Scheduled">Scheduled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block font-semibold text-slate-400 uppercase tracking-wider">Category</Label>
                    <Select value={filterCategory} onValueChange={setFilterCategory}>
                      <SelectTrigger className="h-9 text-sm bg-slate-900 border-slate-800 text-slate-100"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                        <SelectItem value="all">All Categories</SelectItem>
                        {uniqueCategories.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-xs mb-1.5 block font-semibold text-slate-400 uppercase tracking-wider">Date</Label>
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-9 gap-1.5 text-sm w-full justify-start bg-slate-900 border-slate-800 text-slate-200 hover:bg-slate-800"
                      onClick={() => setDateRangeOpen(true)}
                    >
                      <Calendar className="h-3.5 w-3.5 flex-shrink-0 text-slate-400" />
                      <span className="truncate flex-1 text-left">{dateLabel ?? "Pick date or range"}</span>
                      {dateLabel && (
                        <X className="h-3 w-3 flex-shrink-0 text-slate-400 hover:text-rose-400"
                          onClick={(e) => { e.stopPropagation(); setFilterDateFrom(""); setFilterDateTo(""); }} />
                      )}
                    </Button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Sort by:</Label>
                    <Select value={sortBy} onValueChange={setSortBy}>
                      <SelectTrigger className="h-8 text-sm w-36 bg-slate-900 border-slate-800 text-slate-100"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                        <SelectItem value="newest">Newest first</SelectItem>
                        <SelectItem value="oldest">Oldest first</SelectItem>
                        <SelectItem value="views">Most views</SelectItem>
                        <SelectItem value="title">Title A–Z</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {activeCount > 0 && (
                    <Button variant="ghost" size="sm" className="gap-1 text-xs text-purple-400 hover:text-purple-300 h-8" onClick={resetFilters}>
                      <X className="h-3 w-3" />Clear filters
                    </Button>
                  )}
                </div>
              </CardHeader>
            )}

            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-20 text-slate-400 gap-3">
                  <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
                  <span className="font-medium text-sm">Loading video assets from server...</span>
                </div>
              ) : contents.length === 0 ? (
                <div className="text-center py-20 text-slate-500">
                  <Video className="h-12 w-12 mx-auto mb-3 opacity-40 text-purple-400" />
                  <p className="font-semibold text-slate-300">No video content found</p>
                  <p className="text-xs text-slate-500 mt-1">Try adjusting your search or active filters</p>
                  <Button variant="link" className="text-purple-400 mt-2 font-medium" onClick={resetFilters}>Reset filters</Button>
                </div>
              ) : (
                <Table>
                  <TableHeader className="bg-slate-950/80 border-b border-slate-800/80">
                    <TableRow className="border-b border-slate-800/80 hover:bg-transparent">
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Video Asset</TableHead>
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Category</TableHead>
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Status</TableHead>
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Views</TableHead>
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Duration</TableHead>
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Date Added</TableHead>
                      <TableHead className="text-right font-bold text-slate-400 uppercase tracking-wider text-xs">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {contents.map((content) => (
                      <TableRow key={content.id} className="hover:bg-slate-800/40 border-b border-slate-800/60 transition-colors group cursor-pointer">
                        <TableCell onClick={() => setPlayingVideo(content)}>
                          <div className="flex items-center gap-3">
                            <div className="h-16 w-24 rounded-xl bg-slate-950 flex items-center justify-center flex-shrink-0 relative overflow-hidden group/thumb shadow-md border border-slate-800">
                              {content.thumbnailUrl ? (
                                <img src={content.thumbnailUrl} alt={content.title} className="w-full h-full object-cover" />
                              ) : (
                                <Video className="h-6 w-6 text-purple-400 opacity-60" />
                              )}
                              <div className="absolute inset-0 bg-black/0 group-hover/thumb:bg-black/40 transition-colors flex items-center justify-center">
                                <Play className="h-7 w-7 text-white opacity-0 group-hover/thumb:opacity-100 transition-opacity fill-white" />
                              </div>
                              <span className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] px-1 rounded font-mono">{content.duration}</span>
                            </div>
                            <div>
                              <div className="font-semibold text-slate-100 text-sm group-hover:text-purple-400 transition-colors">{content.title}</div>
                              {((content.encodeProgress !== undefined && content.encodeProgress < 100) ||
                                ["Pending", "pending", "Processing", "processing", "Encoding", "encoding", "Uploading", "uploading"].includes(content.status)) ? (
                                <div className="mt-1 space-y-1">
                                  <div className="w-36 bg-slate-950 border border-slate-800 rounded-full h-2 overflow-hidden relative">
                                    <div
                                      className="bg-gradient-to-r from-purple-600 to-indigo-500 h-full transition-all duration-500 rounded-full"
                                      style={{ width: `${Math.max(content.encodeProgress ?? 35, 10)}%` }}
                                    />
                                  </div>
                                  <div className="text-[10px] font-semibold text-purple-400 flex items-center gap-1">
                                    <Loader2 className="h-3 w-3 animate-spin text-purple-400" />
                                    <span>
                                      {content.encodeProgress !== undefined && content.encodeProgress > 0
                                        ? `${content.encodeProgress}% uploaded / encoding`
                                        : `${content.status} · Processing stream...`}
                                    </span>
                                  </div>
                                </div>
                              ) : content.premium ? (
                                <Badge variant="outline" className="mt-1 text-[10px] bg-purple-950/80 border-purple-800/60 text-purple-300">Premium</Badge>
                              ) : null}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-slate-400 text-sm">{content.category}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={`text-xs font-mono ${content.status === "Published" || content.status === "published"
                            ? "bg-emerald-950/80 border-emerald-800/60 text-emerald-400"
                            : content.status === "Draft" || content.status === "draft"
                              ? "bg-slate-800 border-slate-700 text-slate-300"
                              : "bg-amber-950/80 border-amber-800/60 text-amber-400"
                            }`}>
                            {content.status} {content.encodeProgress !== undefined ? `(${content.encodeProgress}%)` : ""}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-slate-300 font-medium text-sm">{content.views}</TableCell>
                        <TableCell className="text-slate-400 font-mono text-xs">{content.duration}</TableCell>
                        <TableCell className="text-slate-400 text-sm">{content.date}</TableCell>
                        <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800"><MoreVertical className="h-4 w-4" /></Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="bg-slate-900/95 border border-slate-800 shadow-2xl backdrop-blur-xl">
                              <DropdownMenuItem onClick={() => setPlayingVideo(content)}>
                                <Play className="mr-2 h-4 w-4 fill-purple-400 text-purple-400" />Play Video
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => setViewContent(content)}>
                                <Eye className="mr-2 h-4 w-4 text-slate-300" />View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => setEditContent(content)}>
                                <Edit className="mr-2 h-4 w-4 text-slate-300" />Edit Content
                              </DropdownMenuItem>
                              {content.status !== "Published" && content.status !== "published" && (
                                <DropdownMenuItem onClick={() => {
                                  publishVideo(content.id).then(() => loadData(true));
                                }}>
                                  <CheckCircle className="mr-2 h-4 w-4 text-emerald-400" />Publish
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-rose-400 focus:bg-rose-950/40" onClick={() => handleDeleteVideo(content.id)}>
                                <Trash2 className="mr-2 h-4 w-4" />Delete Asset
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
        </TabsContent>

        {/* ── Playlists Tab ── */}
        <TabsContent value="playlists">
          <Card className="border border-slate-800/80 bg-slate-900/60 backdrop-blur-xl shadow-2xl rounded-2xl overflow-hidden">
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-20 text-slate-400 gap-3">
                  <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
                  <span className="font-medium text-sm">Loading playlists...</span>
                </div>
              ) : playlists.length === 0 ? (
                <div className="text-center py-20 text-slate-500">
                  <ListVideo className="h-12 w-12 mx-auto mb-3 opacity-40 text-purple-400" />
                  <p className="font-semibold text-slate-300">No playlists found</p>
                  <Button variant="link" className="text-purple-400 mt-2 font-medium" onClick={() => setNewPlaylistOpen(true)}>Create a new playlist</Button>
                </div>
              ) : (
                <Table>
                  <TableHeader className="bg-slate-950/80 border-b border-slate-800/80">
                    <TableRow className="border-b border-slate-800/80 hover:bg-transparent">
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Playlist Collection</TableHead>
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Videos Count</TableHead>
                      <TableHead className="font-bold text-slate-400 uppercase tracking-wider text-xs">Date Created</TableHead>
                      <TableHead className="text-right font-bold text-slate-400 uppercase tracking-wider text-xs">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {playlists.map((pl) => (
                      <TableRow key={pl.id} className="hover:bg-slate-800/40 border-b border-slate-800/60 transition-colors">
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div
                              className="relative h-14 w-24 rounded-xl bg-slate-950 flex items-center justify-center flex-shrink-0 overflow-hidden cursor-pointer group shadow-md border border-slate-800"
                              onClick={() => setActivePlaylist(pl)}
                            >
                              {pl.thumbnailUrl ? (
                                <img src={pl.thumbnailUrl} alt={pl.title} className="w-full h-full object-cover" />
                              ) : (
                                <ListVideo className="h-6 w-6 text-purple-400 opacity-60" />
                              )}
                              <span className="absolute bottom-1 right-1 bg-black/80 text-white text-[10px] px-1 rounded font-bold">{pl.videos}</span>
                            </div>
                            <div>
                              <button
                                className="font-semibold text-slate-100 text-left hover:text-purple-400 transition-colors text-sm"
                                onClick={() => setActivePlaylist(pl)}
                              >
                                {pl.title}
                              </button>
                              <div className="text-xs text-slate-400 mt-0.5 max-w-xs truncate">{pl.description || "No description provided."}</div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="text-slate-300 font-medium text-sm">{pl.videos} videos</TableCell>
                        <TableCell className="text-slate-400 text-sm">{pl.date}</TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800"><MoreVertical className="h-4 w-4" /></Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="bg-slate-900/95 border border-slate-800 shadow-2xl backdrop-blur-xl">
                              <DropdownMenuItem onClick={() => setActivePlaylist(pl)}>
                                <ListVideo className="mr-2 h-4 w-4 text-purple-400" />Open Playlist
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => setEditPlaylistMeta(pl)}>
                                <Edit className="mr-2 h-4 w-4 text-slate-300" />Edit Details
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-rose-400 focus:bg-rose-950/40" onClick={() => handleDeletePlaylist(pl.id)}>
                                <Trash2 className="mr-2 h-4 w-4" />Delete Playlist
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
        </TabsContent>
      </Tabs>

      {/* ── Top-Right Floating Toast Notification ── */}
      {toast.show && (
        <div className="fixed top-5 right-5 z-[9999] max-w-sm w-full bg-slate-900 text-white border border-red-500/60 shadow-2xl rounded-2xl p-4 flex items-start gap-3 animate-in slide-in-from-top-4 duration-300">
          <div className="h-9 w-9 rounded-full bg-red-950/80 border border-red-800 flex items-center justify-center flex-shrink-0 mt-0.5">
            <AlertCircle className="h-5 w-5 text-red-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-bold text-sm text-white">{toast.title}</h4>
            <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">{toast.message}</p>
          </div>
          <button
            onClick={() => setToast((prev) => ({ ...prev, show: false }))}
            className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
