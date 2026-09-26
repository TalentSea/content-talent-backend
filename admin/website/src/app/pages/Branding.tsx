import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { Badge } from "../components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "../components/ui/popover";
import { HoverCard, HoverCardContent, HoverCardTrigger } from "../components/ui/hover-card";
import { ColorPicker } from "../components/ui/color-picker";
import {
  Upload, Save, Play, CheckCircle, Video, Star, ImagePlus, Check, Plus, Trash2, Search, ChevronUp, ChevronDown, Eye, Loader2,
  Smartphone, Palette, RotateCcw, Sparkles, Layers, Wifi, Battery, Signal, Home, Compass, Film, User, Bell
} from "lucide-react";
import {
  getCreatorBranding,
  updateCreatorBranding,
  uploadCreatorLogo,
  uploadCreatorBanner,
  getFeaturedVideos,
  updateFeaturedVideos,
  addFeaturedVideos,
  reorderFeaturedVideos,
  deleteFeaturedVideo,
  getAvailableVideosForFeatured,
  getMobileAppTheme,
  updateMobileAppTheme,
  MobileAppTheme,
  BackgroundStyleType,
  ApiVideo,
  ApiFeaturedVideoItem,
  ApiAvailableFeaturedVideo,
} from "../services/apiService";

interface FeaturedBannerItem {
  id: number;
  videoId: number;
  title: string;
  category: string;
  duration: string;
  thumbnailUrl: string;
  description: string;
}

function getContrastTextColor(hex: string): string {
  const cleanHex = hex.replace("#", "");
  if (cleanHex.length !== 6) return "#FFFFFF";
  const r = parseInt(cleanHex.substring(0, 2), 16);
  const g = parseInt(cleanHex.substring(2, 4), 16);
  const b = parseInt(cleanHex.substring(4, 6), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.65 ? "#0F172A" : "#FFFFFF";
}

const PRIMARY_COLOR_PRESETS = [
  { name: "Royal Indigo", hex: "#6366F1" },
  { name: "Electric Blue", hex: "#2563EB" },
  { name: "Sky Cyan", hex: "#06B6D4" },
  { name: "Emerald", hex: "#10B981" },
  { name: "Crimson Red", hex: "#EF4444" },
  { name: "Sunset Amber", hex: "#F59E0B" },
  { name: "Deep Violet", hex: "#8B5CF6" },
  { name: "Obsidian Slate", hex: "#0F172A" },
];

const ACCENT_COLOR_PRESETS = [
  { name: "Vivid Rose", hex: "#EC4899" },
  { name: "Neon Orange", hex: "#F97316" },
  { name: "Golden Amber", hex: "#FBBF24" },
  { name: "Lime Glow", hex: "#84CC16" },
  { name: "Cyan Spark", hex: "#38BDF8" },
  { name: "Electric Purple", hex: "#A855F7" },
  { name: "Coral Pink", hex: "#FB7185" },
  { name: "Pure White", hex: "#FFFFFF" },
];

const BACKGROUND_STYLES: {
  value: BackgroundStyleType;
  label: string;
  badge: string;
  description: string;
  bgHex: string;
  cardBg: string;
  textColor: string;
  subtextColor: string;
  borderColor: string;
}[] = [
  {
    value: "dark_slate",
    label: "Midnight Slate (Modern Dark)",
    badge: "Recommended",
    description: "Deep charcoal slate with elevated contrast cards. Standard for premium mobile streaming apps.",
    bgHex: "#0B0F19",
    cardBg: "#161D2B",
    textColor: "#FFFFFF",
    subtextColor: "#94A3B8",
    borderColor: "#1E293B",
  },
  {
    value: "pure_black",
    label: "Pure Black (OLED Cinema)",
    badge: "OLED Pitch",
    description: "True pitch black (#000000). Maximum video contrast, edge-to-edge immersion, and OLED battery savings.",
    bgHex: "#000000",
    cardBg: "#121212",
    textColor: "#FFFFFF",
    subtextColor: "#A1A1AA",
    borderColor: "#27272A",
  },
  {
    value: "clean_white",
    label: "Clean White (Light Editorial)",
    badge: "Light Mode",
    description: "Crisp white canvas (#FFFFFF) with gentle card borders. Ideal for lifestyle and editorial creators.",
    bgHex: "#FFFFFF",
    cardBg: "#F8FAFC",
    textColor: "#0F172A",
    subtextColor: "#64748B",
    borderColor: "#E2E8F0",
  },
  {
    value: "gradient_dark",
    label: "Dark Gradient (Subtle Studio Mesh)",
    badge: "Studio Glow",
    description: "Multi-stop radial dark gradient from deep navy slate to obsidian. Luxury high-end creator look.",
    bgHex: "#0F172A",
    cardBg: "#1E293B",
    textColor: "#FFFFFF",
    subtextColor: "#94A3B8",
    borderColor: "#334155",
  },
];

const THEME_PRESETS: Record<string, {
  primaryColor: string;
  secondaryColor: string;
  activeStateColor: string;
  mainBackgroundColor: string;
  cardBackgroundColor: string;
  primaryTextColor: string;
  secondaryTextColor: string;
  mutedTextColor: string;
  buttonTextColor: string;
}> = {
  "Cinematic Black": { primaryColor: "#E50914", secondaryColor: "#FFD700", activeStateColor: "#E50914", mainBackgroundColor: "#000000", cardBackgroundColor: "#121212", primaryTextColor: "#FFFFFF", secondaryTextColor: "#A0A0AB", mutedTextColor: "#52525B", buttonTextColor: "#FFFFFF" },
  "Midnight Blue": { primaryColor: "#6366F1", secondaryColor: "#EC4899", activeStateColor: "#6366F1", mainBackgroundColor: "#0B0C10", cardBackgroundColor: "#1F2833", primaryTextColor: "#FFFFFF", secondaryTextColor: "#C5C6C7", mutedTextColor: "#666666", buttonTextColor: "#FFFFFF" },
  "Cyber Punk / Anime": { primaryColor: "#00E5FF", secondaryColor: "#FF6D00", activeStateColor: "#00E5FF", mainBackgroundColor: "#0D1117", cardBackgroundColor: "#161B22", primaryTextColor: "#F5F5F5", secondaryTextColor: "#B3B3B3", mutedTextColor: "#707070", buttonTextColor: "#000000" },
  "Clean White": { primaryColor: "#0F172A", secondaryColor: "#3B82F6", activeStateColor: "#0F172A", mainBackgroundColor: "#FFFFFF", cardBackgroundColor: "#F8FAFC", primaryTextColor: "#0F172A", secondaryTextColor: "#64748B", mutedTextColor: "#94A3B8", buttonTextColor: "#FFFFFF" }
};

function getContrastYIQ(hexcolor: string): string {
  const hex = hexcolor.replace("#", "");
  if (hex.length !== 6) return "#FFFFFF";
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  const yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000;
  return (yiq >= 128) ? "#000000" : "#FFFFFF";
}

export default function Branding() {
  // Creator & Studio Identity State
  const [studioName, setStudioName] = useState("");
  const [creatorName, setCreatorName] = useState(""); // backward compatibility
  const [creatorTagline, setCreatorTagline] = useState("");
  const [creatorDescription, setCreatorDescription] = useState("");
  const [bannerPreview, setBannerPreview] = useState<string | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [isSavingIdentity, setIsSavingIdentity] = useState(false);
  const [identityError, setIdentityError] = useState<string | null>(null);

  // Available Videos list from system (for picker modal)
  const [availableSystemVideos, setAvailableSystemVideos] = useState<ApiVideo[]>([]);
  
  // Featured Video Banners List State (Max limit 10)
  const MAX_BANNERS = 10;
  const [featuredBanners, setFeaturedBanners] = useState<FeaturedBannerItem[]>([]);
  const [selectedBannerId, setSelectedBannerId] = useState<number | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Modal State for Adding Featured Video Banners (Multi-Select)
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [selectedVideoIdsForAdd, setSelectedVideoIdsForAdd] = useState<string[]>([]);
  const [modalSearch, setModalSearch] = useState<string>("");

  // Image Preview Modal State (for Banner & Logo Preview)
  const [previewModal, setPreviewModal] = useState<{
    isOpen: boolean;
    title: string;
    url: string;
  }>({
    isOpen: false,
    title: "",
    url: "",
  });

  const [themeMode, setThemeMode] = useState<"preset" | "manual">("preset");
  const [selectedPreset, setSelectedPreset] = useState("Cinematic Black");
  const [manualBrandColor, setManualBrandColor] = useState("#E50914");
  const [manualAccentColor, setManualAccentColor] = useState("#FFD700");
  const [manualBgColor, setManualBgColor] = useState("#000000");
  const [contrastMode, setContrastMode] = useState<"dark" | "light">("dark");
  const [isSavingTheme, setIsSavingTheme] = useState(false);
  const [saveThemeSuccess, setSaveThemeSuccess] = useState(false);
  const [themeError, setThemeError] = useState<string | null>(null);

  const currentThemeAttributes = themeMode === "preset"
    ? THEME_PRESETS[selectedPreset] || THEME_PRESETS["Cinematic Black"]
    : {
        primaryColor: manualBrandColor,
        secondaryColor: manualAccentColor,
        activeStateColor: manualBrandColor,
        mainBackgroundColor: manualBgColor,
        cardBackgroundColor: contrastMode === "dark" ? "#121212" : "#F8FAFC",
        primaryTextColor: contrastMode === "dark" ? "#FFFFFF" : "#0F172A",
        secondaryTextColor: contrastMode === "dark" ? "#A0A0AB" : "#64748B",
        mutedTextColor: contrastMode === "dark" ? "#52525B" : "#94A3B8",
        buttonTextColor: getContrastYIQ(manualBrandColor),
      };

  // Load mobile theme configuration from backend API
  useEffect(() => {
    let isMounted = true;
    const fetchTheme = (retryCount = 0) => {
      getMobileAppTheme()
        .then((theme) => {
          if (!isMounted || !theme) return;
          if (theme.primaryColor) setManualBrandColor(theme.primaryColor);
          if (theme.secondaryColor) setManualAccentColor(theme.secondaryColor);
          if (theme.mainBackgroundColor) setManualBgColor(theme.mainBackgroundColor);

          // Attempt to match against known theme presets
          const match = Object.entries(THEME_PRESETS).find(
            ([_, p]) =>
              p.primaryColor.toLowerCase() === theme.primaryColor?.toLowerCase() &&
              p.mainBackgroundColor.toLowerCase() === theme.mainBackgroundColor?.toLowerCase()
          );
          if (match) {
            setSelectedPreset(match[0]);
            setThemeMode("preset");
          } else {
            setThemeMode("manual");
          }
        })
        .catch((err) => {
          console.warn("Failed to load mobile theme from API:", err);
          if (isMounted && retryCount < 2) {
            setTimeout(() => fetchTheme(retryCount + 1), 3000);
          }
        });
    };
    fetchTheme();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSaveTheme = async () => {
    setThemeError(null);
    setIsSavingTheme(true);
    try {
      await updateMobileAppTheme(currentThemeAttributes);
      setSaveThemeSuccess(true);
      toast.success("Studio theme updated successfully!");
      setTimeout(() => {
        setSaveThemeSuccess(false);
      }, 3000);
    } catch (err: any) {
      console.error("Failed to save mobile app theme:", err);
      const msg = err?.message || "Failed to save mobile app theme.";
      setThemeError(msg);
      toast.error(msg);
    } finally {
      setIsSavingTheme(false);
    }
  };

  const handleResetThemeDefaults = () => {
    setSelectedPreset("Cinematic Black");
    setThemeMode("preset");
    setManualBrandColor("#E50914");
    setManualAccentColor("#FFD700");
    setManualBgColor("#000000");
    setContrastMode("dark");
    toast.success("Theme reset to Cinematic Black preset defaults.");
  };

  // Hidden File Inputs
  const bannerInputRef = useRef<HTMLInputElement>(null);
  const logoInputRef = useRef<HTMLInputElement>(null);

  // Fetch creator branding details from backend
  useEffect(() => {
    getCreatorBranding()
      .then((data) => {
        const name = data.studioName || data.creatorName || "";
        if (name) {
          setStudioName(name);
          setCreatorName(name);
        }
        if (data.tagline) setCreatorTagline(data.tagline);
        if (data.description) setCreatorDescription(data.description);
        if (data.bannerUrl) setBannerPreview(data.bannerUrl);
        if (data.logoUrl) setLogoPreview(data.logoUrl);
      })
      .catch((err) => {
        console.warn("Failed to load branding identity from backend:", err);
      });
  }, []);

  // Fetch featured videos from backend API
  useEffect(() => {
    getFeaturedVideos()
      .then((items) => {
        if (items && items.length > 0) {
          const mapped = items.map((item) => ({
            id: item.id,
            videoId: item.videoId,
            title: item.title,
            category: item.category || "Video",
            duration: item.duration || "00:00",
            thumbnailUrl: item.thumbnailUrl || "",
            description: "",
          }));
          setFeaturedBanners(mapped);
          setSelectedBannerId(mapped[0].id);
        } else {
          setFeaturedBanners([]);
          setSelectedBannerId(null);
        }
      })
      .catch((err) => {
        console.warn("Failed to load featured videos from API:", err);
        setFeaturedBanners([]);
      });
  }, []);

  // Fetch available creator videos for picker modal
  useEffect(() => {
    getAvailableVideosForFeatured()
      .then((res) => {
        if (res.items) {
          const mapped = res.items.map((v) => ({
            id: v.id,
            title: v.title,
            description: "",
            category: v.category || "Video",
            status: "published",
            views: v.views,
            duration: v.duration,
            date: v.createdAt,
            thumbnailUrl: v.thumbnailUrl,
          }));
          setAvailableSystemVideos(mapped as any);
        }
      })
      .catch((err) => {
        console.warn("Failed to fetch available videos for featured:", err);
      });
  }, []);

  // Video options for dropdown selection
  const dropdownVideoOptions = availableSystemVideos.map((v) => ({
    id: v.id,
    title: v.title,
    category: v.category || "Video",
    duration: v.duration || "00:00",
    thumbnailUrl: v.thumbnailUrl || v.mainThumbnailUrl || "",
    description: v.description || "",
  }));

  // Currently active featured banner object
  const activeBanner = featuredBanners.find((b) => b.id === selectedBannerId) || featuredBanners[0] || null;

  const handleBannerSelect = (id: number) => {
    setSelectedBannerId(id);
  };

  const handleBannerUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setBannerPreview(URL.createObjectURL(file));
      try {
        const res = await uploadCreatorBanner(file);
        if (res.bannerUrl) {
          setBannerPreview(res.bannerUrl);
          toast.success("Studio banner uploaded successfully.");
        }
      } catch (err: any) {
        console.warn("Failed to upload creator banner to backend:", err);
        toast.error(err?.message || "Failed to upload creator banner.");
      }
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLogoPreview(URL.createObjectURL(file));
      try {
        const res = await uploadCreatorLogo(file);
        if (res.logoUrl) {
          setLogoPreview(res.logoUrl);
          window.dispatchEvent(new CustomEvent("branding_updated", { detail: { logoUrl: res.logoUrl } }));
          toast.success("Studio logo uploaded successfully.");
        }
      } catch (err: any) {
        console.warn("Failed to upload creator logo to backend:", err);
        toast.error(err?.message || "Failed to upload creator logo.");
      }
    }
  };

  // Open modal handler for multi-select
  const handleOpenAddModal = () => {
    setSelectedVideoIdsForAdd([]);
    setModalSearch("");
    setIsAddModalOpen(true);
    getAvailableVideosForFeatured()
      .then((res) => {
        if (res.items) {
          const mapped = res.items.map((v) => ({
            id: v.id,
            title: v.title,
            description: "",
            category: v.category || "Video",
            status: "published",
            views: v.views,
            duration: v.duration,
            date: v.createdAt,
            thumbnailUrl: v.thumbnailUrl,
          }));
          setAvailableSystemVideos(mapped as any);
        }
      })
      .catch((err) => {
        console.warn("Failed to fetch available videos on modal open:", err);
      });
  };

  // Calculate remaining slots up to MAX_BANNERS (10)
  const remainingSlots = Math.max(0, MAX_BANNERS - featuredBanners.length);

  // Toggle video selection with limit enforcement
  const handleToggleVideoSelection = (vidIdStr: string) => {
    if (selectedVideoIdsForAdd.includes(vidIdStr)) {
      setSelectedVideoIdsForAdd((prev) => prev.filter((id) => id !== vidIdStr));
    } else {
      if (selectedVideoIdsForAdd.length >= remainingSlots) {
        return; // Exceeds available limit of 10
      }
      setSelectedVideoIdsForAdd((prev) => [...prev, vidIdStr]);
    }
  };

  // Submit multiple selected video banners to local state
  const handleAddBannerSubmit = () => {
    if (selectedVideoIdsForAdd.length === 0 || remainingSlots <= 0) return;

    const toAddIds = selectedVideoIdsForAdd.slice(0, remainingSlots);
    const newItems: FeaturedBannerItem[] = [];

    toAddIds.forEach((vidIdStr, index) => {
      const matchedId = parseInt(vidIdStr, 10);
      if (isNaN(matchedId)) return;

      // Prevent duplicate video additions
      const isAlreadyInList = featuredBanners.some((b) => Number(b.videoId) === matchedId);
      if (isAlreadyInList) return;

      const matched = dropdownVideoOptions.find((o) => Number(o.id) === matchedId);
      if (matched) {
        newItems.push({
          id: Date.now() + index,
          videoId: matched.id,
          title: matched.title,
          category: matched.category,
          duration: matched.duration,
          thumbnailUrl: matched.thumbnailUrl,
          description: matched.description || "Highlighted video banner",
        });
      }
    });

    if (newItems.length > 0) {
      setFeaturedBanners((prev) => [...prev, ...newItems]);
      if (!selectedBannerId) {
        setSelectedBannerId(newItems[0].id);
      }
    }

    // Reset Form & Close Modal
    setIsAddModalOpen(false);
    setSelectedVideoIdsForAdd([]);
  };

  // Delete banner locally (synced when Save Changes is clicked)
  const handleDeleteBanner = (id: number, _videoId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = featuredBanners.filter((b) => b.id !== id);
    setFeaturedBanners(updated);
    if (selectedBannerId === id && updated.length > 0) {
      setSelectedBannerId(updated[0].id);
    }
    toast.info("Banner removed from list. Click 'Save Banners' to persist changes.");
  };

  // Move banner up locally
  const handleMoveUp = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (index <= 0) return;
    setFeaturedBanners((prev) => {
      const next = [...prev];
      const temp = next[index - 1];
      next[index - 1] = next[index];
      next[index] = temp;
      return next;
    });
  };

  // Move banner down locally
  const handleMoveDown = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (index >= featuredBanners.length - 1) return;
    setFeaturedBanners((prev) => {
      const next = [...prev];
      const temp = next[index + 1];
      next[index + 1] = next[index];
      next[index] = temp;
      return next;
    });
  };

  // Featured Videos Section Save Changes Handler (Batch sync to API)
  const [saveFeaturedBannersSuccess, setSaveFeaturedBannersSuccess] = useState(false);
  const [isSavingFeaturedBanners, setIsSavingFeaturedBanners] = useState(false);

  const handleSaveFeaturedBanners = async () => {
    setIsSavingFeaturedBanners(true);
    try {
      const videoIds = featuredBanners.map((b) => b.videoId).filter(Boolean);
      await updateFeaturedVideos(videoIds);
      setSaveFeaturedBannersSuccess(true);
      toast.success("Featured video banners saved successfully.");
      setTimeout(() => {
        setSaveFeaturedBannersSuccess(false);
      }, 3000);
    } catch (err: any) {
      console.warn("Failed to save featured videos changes to backend:", err);
      toast.error(err?.message || "Something went wrong while saving featured banners.");
    } finally {
      setIsSavingFeaturedBanners(false);
    }
  };

  // Creator & Studio Identity Section Save Changes Handler
  const handleSaveChanges = async () => {
    setIdentityError(null);
    const trimmedStudioName = (studioName || creatorName).trim();
    if (!trimmedStudioName) {
      setIdentityError("Studio / Channel Name is required.");
      return;
    }
    setIsSavingIdentity(true);
    try {
      const updated = await updateCreatorBranding({
        studio_name: trimmedStudioName,
        tagline: creatorTagline.trim(),
        description: creatorDescription.trim(),
      });
      if (updated.studioName) {
        setStudioName(updated.studioName);
        setCreatorName(updated.studioName);
        try {
          const raw = localStorage.getItem("admin_profile");
          if (raw) {
            const admin = JSON.parse(raw);
            admin.studio_name = updated.studioName;
            if (updated.tagline) admin.tagline = updated.tagline;
            if (updated.logoUrl) admin.avatar_url = updated.logoUrl;
            localStorage.setItem("admin_profile", JSON.stringify(admin));
          }
        } catch {
          // ignore localStorage parsing errors
        }
        window.dispatchEvent(new CustomEvent("branding_updated", { detail: updated }));
      }
      setSaveSuccess(true);
      toast.success("Studio identity updated successfully.");
      setTimeout(() => {
        setSaveSuccess(false);
      }, 3000);
    } catch (err: any) {
      console.error("Failed to save creator branding changes:", err);
      const msg = err?.message || "Failed to save creator studio branding.";
      setIdentityError(msg);
      toast.error(msg);
    } finally {
      setIsSavingIdentity(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Add Featured Video Banners Dialog Modal (Multi-Select with 10 Banners Limit) */}
      <Dialog open={isAddModalOpen} onOpenChange={setIsAddModalOpen}>
        <DialogContent className="max-w-lg bg-white border border-slate-200 text-slate-900 shadow-2xl rounded-2xl">
          <DialogHeader className="pr-8">
            <div className="flex items-center justify-between gap-2">
              <DialogTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Plus className="h-5 w-5 text-slate-700" />
                Add Featured Video Banners
              </DialogTitle>
              <Badge variant="outline" className={`text-xs px-2.5 py-0.5 font-semibold ${
                featuredBanners.length >= MAX_BANNERS
                  ? "border-amber-200 bg-amber-50 text-amber-800"
                  : "border-slate-200 bg-slate-100 text-slate-700"
              }`}>
                {featuredBanners.length} / {MAX_BANNERS} Banners
              </Badge>
            </div>
            <DialogDescription className="text-sm text-slate-500 mt-1">
              Select videos to feature as hero banners (up to {MAX_BANNERS} total).
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Limit Warning Alert if max 10 reached */}
            {featuredBanners.length >= MAX_BANNERS ? (
              <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs flex items-center gap-2 font-medium">
                <span>Maximum limit of 10 featured banners reached. Delete an existing banner to add new ones.</span>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-sm font-semibold text-slate-800 block">
                    Select Videos <span className="text-rose-500">*</span>
                  </Label>
                  <span className="text-xs text-slate-500 font-medium">
                    Selected: <span className="text-slate-900 font-bold">{selectedVideoIdsForAdd.length}</span> / {remainingSlots} Available
                  </span>
                </div>

                {/* Search filter for videos */}
                <div className="relative mb-3">
                  <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    placeholder="Search videos by title or category..."
                    value={modalSearch}
                    onChange={(e) => setModalSearch(e.target.value)}
                    className="pl-10 bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 text-sm h-10 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl"
                  />
                </div>

                {/* Scrollable list of video cards with checkboxes */}
                <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
                  {(() => {
                    const unaddedOptions = dropdownVideoOptions.filter(
                      (opt) => !featuredBanners.some((b) => Number(b.videoId) === Number(opt.id))
                    );

                    const filteredOptions = unaddedOptions.filter(
                      (opt) =>
                        !modalSearch.trim() ||
                        opt.title.toLowerCase().includes(modalSearch.toLowerCase()) ||
                        opt.category.toLowerCase().includes(modalSearch.toLowerCase())
                    );

                    if (unaddedOptions.length === 0) {
                      return (
                        <div className="text-center py-8 text-slate-500 text-xs bg-slate-50 rounded-xl border border-slate-200 p-4">
                          {dropdownVideoOptions.length === 0
                            ? "No uploaded videos found in your system library."
                            : "All available videos have already been added as featured banners."}
                        </div>
                      );
                    }

                    if (filteredOptions.length === 0) {
                      return (
                        <div className="text-center py-8 text-slate-500 text-xs bg-slate-50 rounded-xl border border-slate-200 p-4">
                          No matching videos found for "{modalSearch}".
                        </div>
                      );
                    }

                    return filteredOptions.map((opt) => {
                      const isSelected = selectedVideoIdsForAdd.includes(String(opt.id));
                      const isAtMaxLimit = !isSelected && selectedVideoIdsForAdd.length >= remainingSlots;

                      return (
                        <div
                          key={opt.id}
                          onClick={() => !isAtMaxLimit && handleToggleVideoSelection(String(opt.id))}
                          className={`flex items-center gap-3 p-2.5 rounded-xl border transition-all ${
                            isAtMaxLimit
                              ? "opacity-50 cursor-not-allowed border-slate-200 bg-slate-50"
                              : isSelected
                              ? "border-slate-900 bg-slate-100 shadow-xs cursor-pointer"
                              : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 cursor-pointer"
                          }`}
                        >
                          {/* Checkbox Selection Indicator */}
                          <div className="flex-shrink-0">
                            <div
                              className={`h-4.5 w-4.5 rounded border flex items-center justify-center transition-colors ${
                                isSelected
                                  ? "border-slate-900 bg-slate-900 text-white"
                                  : isAtMaxLimit
                                  ? "border-slate-200 bg-slate-100"
                                  : "border-slate-300 bg-white hover:border-slate-500"
                              }`}
                            >
                              {isSelected && (
                                <Check className="h-3 w-3 text-white stroke-[3]" />
                              )}
                            </div>
                          </div>

                          {/* Video Thumbnail Box */}
                          <div className="h-12 w-20 rounded-lg bg-slate-100 flex-shrink-0 overflow-hidden border border-slate-200 relative shadow-xs">
                            {opt.thumbnailUrl ? (
                              <img src={opt.thumbnailUrl} alt={opt.title} className="w-full h-full object-cover" />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <Video className="h-4 w-4 text-slate-400" />
                              </div>
                            )}
                            <span className="absolute bottom-0.5 right-0.5 bg-black/85 text-white text-[9px] px-1 py-0.5 rounded font-mono font-medium">
                              {opt.duration}
                            </span>
                          </div>

                          {/* Video Title & Metadata */}
                          <div className="flex-1 min-w-0">
                            <div className={`text-xs font-bold truncate ${isSelected ? "text-slate-900" : "text-slate-800"}`}>
                              {opt.title}
                            </div>
                            <div className="flex items-center gap-1.5 text-[11px] text-slate-500 mt-0.5">
                              <span className="text-slate-700 font-medium">{opt.category}</span>
                              <span className="text-slate-400">•</span>
                              <span>{opt.duration}</span>
                            </div>
                          </div>
                        </div>
                      );
                    });
                  })()}
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="gap-2 sm:gap-0 pt-3 border-t border-slate-100">
            <Button
              variant="outline"
              onClick={() => setIsAddModalOpen(false)}
              className="border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-xs rounded-xl shadow-xs"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddBannerSubmit}
              disabled={selectedVideoIdsForAdd.length === 0 || remainingSlots <= 0}
              className="bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs gap-1.5 rounded-xl shadow-xs disabled:opacity-40"
            >
              <Plus className="h-4 w-4" />
              {selectedVideoIdsForAdd.length > 1
                ? `Add ${selectedVideoIdsForAdd.length} Banners`
                : "Add Banner"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Image Preview Modal (Banner & Logo) */}
      <Dialog
        open={previewModal.isOpen}
        onOpenChange={(open) => setPreviewModal((prev) => ({ ...prev, isOpen: open }))}
      >
        <DialogContent className="max-w-3xl bg-white border border-slate-200 text-slate-900 shadow-2xl p-6 rounded-2xl">
          <DialogHeader className="pr-8">
            <DialogTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Eye className="h-5 w-5 text-slate-700" />
              {previewModal.title}
            </DialogTitle>
          </DialogHeader>
          <div className="mt-4 flex items-center justify-center p-4 bg-slate-50 border border-slate-200 rounded-xl overflow-hidden min-h-[220px]">
            {previewModal.url ? (
              <img
                src={previewModal.url}
                alt={previewModal.title}
                className="max-h-[70vh] w-auto max-w-full object-contain rounded-lg shadow-xs"
              />
            ) : (
              <p className="text-slate-400 text-sm">No preview image available</p>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Branding & Customization</h1>
        <p className="text-slate-500 mt-1 font-normal text-sm">
          Customize your studio brand, assets, and featured video banners.
        </p>
      </div>

      {/* Main Content Sections */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        <div className="xl:col-span-8 space-y-6">
        {/* Creator Studio & App Identity Card */}
        <Card className="border border-slate-200/80 bg-white shadow-xs rounded-2xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center shrink-0">
                  <Star className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg font-bold text-slate-900">Creator Studio & App Identity</CardTitle>
                    <Badge variant="outline" className="text-xs px-2.5 py-0.5 border-slate-200 bg-slate-100 text-slate-700 font-semibold">
                      Public Brand
                    </Badge>
                  </div>
                </div>
              </div>
              <Button
                onClick={handleSaveChanges}
                disabled={isSavingIdentity}
                className={`gap-2 font-semibold text-sm h-10 px-4 transition-all duration-200 shrink-0 rounded-xl shadow-xs ${
                  saveSuccess
                    ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                    : "bg-slate-900 hover:bg-slate-800 text-white"
                }`}
              >
                {isSavingIdentity ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : saveSuccess ? (
                  <>
                    <CheckCircle className="h-4 w-4" />
                    Saved!
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save Studio Identity
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-5 pt-6">
            {identityError && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2 font-medium">
                <span>⚠️ {identityError}</span>
              </div>
            )}
            {saveSuccess && (
              <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center gap-2 font-medium">
                <span>✓ Studio branding successfully saved and synchronized across your platform.</span>
              </div>
            )}

            {/* Studio / Channel Name */}
            <div>
              <Label htmlFor="studio-name" className="text-sm font-semibold text-slate-800 block">
                Studio / Channel Name <span className="text-rose-500">*</span>
              </Label>
              <Input
                id="studio-name"
                value={studioName || creatorName}
                onChange={(e) => {
                  setStudioName(e.target.value);
                  setCreatorName(e.target.value);
                  if (identityError) setIdentityError(null);
                }}
                placeholder="e.g. Creator Academy"
                className="mt-2 h-11 text-sm font-medium bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
              />
            </div>

            {/* Studio Tagline */}
            <div>
              <Label htmlFor="creator-tagline" className="text-sm font-semibold text-slate-800 block">
                Studio Tagline / Slogan
              </Label>
              <Input
                id="creator-tagline"
                value={creatorTagline}
                onChange={(e) => setCreatorTagline(e.target.value)}
                placeholder="e.g. Learn from industry leaders"
                className="mt-2 h-11 text-sm font-medium bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
              />
            </div>

            {/* Studio Description */}
            <div>
              <Label htmlFor="creator-desc" className="text-sm font-semibold text-slate-800 block">
                Studio Description / Channel Bio
              </Label>
              <Textarea
                id="creator-desc"
                rows={4}
                value={creatorDescription}
                onChange={(e) => setCreatorDescription(e.target.value)}
                placeholder="Tell your subscribers and viewers about your courses, content offerings, and studio mission..."
                className="mt-2 text-sm font-medium bg-white border-slate-200 text-slate-900 placeholder:text-slate-400 focus:border-slate-900 focus:ring-1 focus:ring-slate-900 rounded-xl shadow-xs"
              />
            </div>

            {/* Studio Banner & Studio Logo Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-3 border-t border-slate-100">
              {/* Studio Banner Slot */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-sm font-semibold text-slate-800 block">
                    Studio Cover Banner
                  </Label>
                  {bannerPreview && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPreviewModal({
                          isOpen: true,
                          title: "Studio Banner Preview",
                          url: bannerPreview,
                        });
                      }}
                      className="h-7 px-2.5 text-xs font-semibold gap-1.5 border-slate-200 bg-white text-slate-700 hover:bg-slate-50 rounded-lg shadow-xs"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      Preview
                    </Button>
                  )}
                </div>
                <input
                  type="file"
                  ref={bannerInputRef}
                  onChange={handleBannerUpload}
                  accept="image/*"
                  className="hidden"
                />
                <div
                  onClick={() => bannerInputRef.current?.click()}
                  className="relative group cursor-pointer border-2 border-dashed border-slate-200 hover:border-slate-400 bg-slate-50/50 rounded-xl overflow-hidden h-32 flex flex-col items-center justify-center transition-all p-2"
                >
                  {bannerPreview ? (
                    <>
                      <img
                        src={bannerPreview}
                        alt="Studio Banner"
                        className="w-full h-full object-cover rounded-lg opacity-90 group-hover:opacity-100 transition-opacity"
                      />
                      <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity text-white text-sm font-semibold gap-2 rounded-xl">
                        <Upload className="h-4 w-4" />
                        Change Banner
                      </div>
                    </>
                  ) : (
                    <div className="text-center p-3">
                      <ImagePlus className="h-7 w-7 mx-auto text-slate-400 group-hover:text-slate-600 mb-1.5" />
                      <p className="text-sm text-slate-700 font-semibold">Click to upload Banner</p>
                      <p className="text-xs text-slate-400 mt-1">Recommended 1200×400px (JPG, PNG, WebP)</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Studio Logo Slot */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label className="text-sm font-semibold text-slate-800 block">
                    Studio Logo / App Icon
                  </Label>
                  {logoPreview && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPreviewModal({
                          isOpen: true,
                          title: "Studio Logo Preview",
                          url: logoPreview,
                        });
                      }}
                      className="h-7 px-2.5 text-xs font-semibold gap-1.5 border-slate-200 bg-white text-slate-700 hover:bg-slate-50 rounded-lg shadow-xs"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      Preview
                    </Button>
                  )}
                </div>
                <input
                  type="file"
                  ref={logoInputRef}
                  onChange={handleLogoUpload}
                  accept="image/*"
                  className="hidden"
                />
                <div
                  onClick={() => logoInputRef.current?.click()}
                  className="relative group cursor-pointer border-2 border-dashed border-slate-200 hover:border-slate-400 bg-slate-50/50 rounded-xl h-32 flex items-center justify-center transition-all p-3"
                >
                  <div className="flex items-center gap-4 w-full">
                    <div className="h-16 w-16 rounded-xl bg-slate-900 flex items-center justify-center text-white text-2xl font-bold shadow-xs flex-shrink-0 overflow-hidden relative">
                      {logoPreview ? (
                        <img src={logoPreview} alt="Studio Logo" className="w-full h-full object-cover" />
                      ) : (
                        (studioName || creatorName || "ST").slice(0, 2).toUpperCase()
                      )}
                    </div>
                    <div className="min-w-0 flex-1 space-y-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          logoInputRef.current?.click();
                        }}
                        className="w-full gap-2 border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-sm h-9 px-3 font-semibold rounded-xl shadow-xs"
                      >
                        <Upload className="h-4 w-4 text-slate-500" />
                        Upload Logo
                      </Button>
                      <p className="text-xs text-slate-500 font-medium truncate">
                        PNG, SVG, or WebP (512×512px)
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Mobile App Appearance & Theme Card */}
        <Card className="border border-slate-200/80 bg-white shadow-xs rounded-2xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0">
                  <Smartphone className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <CardTitle className="text-lg font-bold text-slate-900">Mobile App Appearance & Theme</CardTitle>
                   {/* <Badge variant="outline" className="text-xs px-2.5 py-0.5 border-indigo-200 bg-indigo-50 text-indigo-700 font-semibold">
                      iOS & Android
                    </Badge>*/}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Customize brand colors, accent badges, and background styles for your white-labeled mobile applications.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResetThemeDefaults}
                  disabled={isSavingTheme}
                  className="gap-1.5 text-xs text-slate-600 hover:text-slate-900 border-slate-200 h-9 rounded-xl font-medium"
                >
                  <RotateCcw className="h-3.5 w-3.5 text-slate-400" />
                  Reset Defaults
                </Button>
                <Button
                  onClick={handleSaveTheme}
                  disabled={isSavingTheme}
                  className={`gap-2 font-semibold text-sm h-9 px-4 transition-all duration-200 rounded-xl shadow-xs ${
                    saveThemeSuccess
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                      : "bg-slate-900 hover:bg-slate-800 text-white"
                  }`}
                >
                  {isSavingTheme ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : saveThemeSuccess ? (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Saved!
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      Save Mobile Theme
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-6 space-y-6">
            {themeError && (
              <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center gap-2 font-medium">
                <span>⚠️ {themeError}</span>
              </div>
            )}

            <div className="space-y-7">
              {/* Controls Column */}
              <div className="space-y-7">
                {/* Theme Mode Toggle */}
                <div className="flex items-center p-1 bg-slate-100/80 rounded-xl w-fit">
                  <button
                    onClick={() => setThemeMode("preset")}
                    className={`px-5 py-2 text-sm font-bold rounded-lg transition-all ${themeMode === "preset" ? "bg-white shadow-sm text-slate-900" : "text-slate-500 hover:text-slate-900"}`}
                  >
                    Theme Presets
                  </button>
                  <button
                    onClick={() => setThemeMode("manual")}
                    className={`px-5 py-2 text-sm font-bold rounded-lg transition-all ${themeMode === "manual" ? "bg-white shadow-sm text-slate-900" : "text-slate-500 hover:text-slate-900"}`}
                  >
                    Manual Config
                  </button>
                </div>

                {themeMode === "preset" ? (
                  <div className="space-y-3">
                    <Label className="text-sm font-bold text-slate-900 flex items-center gap-2">Select a Theme Package</Label>
                    <p className="text-xs text-slate-500 mt-0.5">Loads a pre-tested set of colors matching a specific niche.</p>
                    <Select value={selectedPreset} onValueChange={setSelectedPreset}>
                      <SelectTrigger className="w-full h-11 bg-white border-slate-200 rounded-xl focus:border-slate-900">
                        <SelectValue placeholder="Select preset" />
                      </SelectTrigger>
                      <SelectContent className="bg-white rounded-xl shadow-xl border-slate-200 z-50">
                        {Object.keys(THEME_PRESETS).map(preset => (
                          <SelectItem key={preset} value={preset} className="py-2.5 cursor-pointer font-medium">{preset}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ) : (
                  <div className="space-y-7">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                      {/* 1. Brand Color */}
                      <div className="space-y-3 flex flex-col h-full">
                        <Label className="text-sm font-bold text-slate-900">Brand Color</Label>
                        <p className="text-xs text-slate-500 mt-0.5">Main buttons & icons.</p>
                        <div className="flex items-center gap-3 p-3 bg-slate-50/70 border border-slate-200/80 rounded-xl">
                          <HoverCard openDelay={0} closeDelay={300}>
                            <HoverCardTrigger asChild>
                              <div
                                className="w-10 h-10 rounded-full border-2 border-slate-200 shadow-sm cursor-pointer transition-transform hover:scale-110 shrink-0"
                                style={{ backgroundColor: manualBrandColor }}
                              />
                            </HoverCardTrigger>
                            <HoverCardContent side="top" align="start" className="w-auto p-0 border-none shadow-none bg-transparent">
                              <ColorPicker color={manualBrandColor} onChange={setManualBrandColor} />
                            </HoverCardContent>
                          </HoverCard>
                          <div className="flex-1 space-y-1 min-w-0">
                            <Label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Hex Code</Label>
                            <Input
                              type="text"
                              value={manualBrandColor.toUpperCase()}
                              onChange={(e) => { let v = e.target.value; if (!v.startsWith("#")) v = "#" + v; setManualBrandColor(v.slice(0, 7)); }}
                              className="w-full bg-white font-mono text-xs uppercase h-8 border-slate-200 rounded-lg focus:border-slate-900 px-2"
                              maxLength={7}
                            />
                          </div>
                        </div>
                      </div>

                      {/* 2. Accent Color */}
                      <div className="space-y-3 flex flex-col h-full">
                        <Label className="text-sm font-bold text-slate-900">Accent Color</Label>
                        <p className="text-xs text-slate-500 mt-0.5">Badges & highlights.</p>
                        <div className="flex items-center gap-3 p-3 bg-slate-50/70 border border-slate-200/80 rounded-xl">
                          <HoverCard openDelay={0} closeDelay={300}>
                            <HoverCardTrigger asChild>
                              <div
                                className="w-10 h-10 rounded-full border-2 border-slate-200 shadow-sm cursor-pointer transition-transform hover:scale-110 shrink-0"
                                style={{ backgroundColor: manualAccentColor }}
                              />
                            </HoverCardTrigger>
                            <HoverCardContent side="top" align="center" className="w-auto p-0 border-none shadow-none bg-transparent">
                              <ColorPicker color={manualAccentColor} onChange={setManualAccentColor} />
                            </HoverCardContent>
                          </HoverCard>
                          <div className="flex-1 space-y-1 min-w-0">
                            <Label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Hex Code</Label>
                            <Input
                              type="text"
                              value={manualAccentColor.toUpperCase()}
                              onChange={(e) => { let v = e.target.value; if (!v.startsWith("#")) v = "#" + v; setManualAccentColor(v.slice(0, 7)); }}
                              className="w-full bg-white font-mono text-xs uppercase h-8 border-slate-200 rounded-lg focus:border-slate-900 px-2"
                              maxLength={7}
                            />
                          </div>
                        </div>
                      </div>

                      {/* 3. Background Color */}
                      <div className="space-y-3 flex flex-col h-full">
                        <Label className="text-sm font-bold text-slate-900">Background</Label>
                        <p className="text-xs text-slate-500 mt-0.5">Main canvas color.</p>
                        <div className="flex items-center gap-3 p-3 bg-slate-50/70 border border-slate-200/80 rounded-xl">
                          <HoverCard openDelay={0} closeDelay={300}>
                            <HoverCardTrigger asChild>
                              <div
                                className="w-10 h-10 rounded-full border-2 border-slate-200 shadow-sm cursor-pointer transition-transform hover:scale-110 shrink-0"
                                style={{ backgroundColor: manualBgColor }}
                              />
                            </HoverCardTrigger>
                            <HoverCardContent side="top" align="end" className="w-auto p-0 border-none shadow-none bg-transparent">
                              <ColorPicker color={manualBgColor} onChange={setManualBgColor} />
                            </HoverCardContent>
                          </HoverCard>
                          <div className="flex-1 space-y-1 min-w-0">
                            <Label className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Hex Code</Label>
                            <Input
                              type="text"
                              value={manualBgColor.toUpperCase()}
                              onChange={(e) => { let v = e.target.value; if (!v.startsWith("#")) v = "#" + v; setManualBgColor(v.slice(0, 7)); }}
                              className="w-full bg-white font-mono text-xs uppercase h-8 border-slate-200 rounded-lg focus:border-slate-900 px-2"
                              maxLength={7}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* 4. Contrast Mode Toggle */}
                    <div className="space-y-3 flex flex-col">
                      <Label className="text-sm font-bold text-slate-900">Text & Card Contrast</Label>
                      <p className="text-xs text-slate-500 mt-0.5">Injects tested text and overlay colors based on your choice.</p>
                      <div className="flex items-center gap-3 max-w-md">
                        <button
                          onClick={() => setContrastMode("dark")}
                          className={`flex-1 py-3 text-sm font-bold rounded-xl border-2 transition-all ${contrastMode === "dark" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"}`}
                        >
                          Dark Text/Cards
                        </button>
                        <button
                          onClick={() => setContrastMode("light")}
                          className={`flex-1 py-3 text-sm font-bold rounded-xl border-2 transition-all ${contrastMode === "light" ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"}`}
                        >
                          Light Text/Cards
                        </button>
                      </div>
                    </div>
                  </div>
                )}

              </div>

            </div>
          </CardContent>
        </Card>

        {/* Featured Videos Card */}
        <Card className="border border-slate-200/80 bg-white shadow-xs rounded-2xl">
          <CardHeader className="border-b border-slate-100 pb-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center shrink-0">
                  <Video className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle className="text-lg font-bold text-slate-900">Featured Videos</CardTitle>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                <Button
                  onClick={handleSaveFeaturedBanners}
                  disabled={isSavingFeaturedBanners}
                  className={`gap-2 font-semibold text-sm h-10 px-4 transition-all duration-200 rounded-xl shadow-xs ${
                    saveFeaturedBannersSuccess
                      ? "bg-emerald-600 hover:bg-emerald-500 text-white"
                      : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                  }`}
                >
                  {saveFeaturedBannersSuccess ? (
                    <>
                      <CheckCircle className="h-4 w-4" />
                      Saved!
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4" />
                      Save Changes
                    </>
                  )}
                </Button>
                <Button
                  onClick={handleOpenAddModal}
                  className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm gap-2 h-10 px-4 rounded-xl shadow-xs"
                >
                  <Plus className="h-4 w-4" />
                  Add
                </Button>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-6 pt-6">
            {/* Featured Video Banners List */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <Label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                  Featured Banners
                </Label>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 font-medium">
                    <strong className="text-slate-900">{featuredBanners.length}</strong> / {MAX_BANNERS} Banners Configured
                  </span>
                  {featuredBanners.length >= MAX_BANNERS && (
                    <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-800 text-[10px] px-1.5 py-0">
                      Limit Reached
                    </Badge>
                  )}
                </div>
              </div>

              <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                {featuredBanners.length === 0 ? (
                  <div className="text-center py-8 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                    <Video className="h-8 w-8 mx-auto text-slate-400 mb-2 stroke-[1.5]" />
                    <p className="text-sm font-medium text-slate-700">No featured banners configured</p>
                    <p className="text-xs text-slate-500 mt-1">Click the + Add button to select a video and add its banner</p>
                    <Button
                      onClick={handleOpenAddModal}
                      variant="outline"
                      size="sm"
                      className="mt-3 border-slate-200 bg-white text-slate-700 hover:bg-slate-50 text-xs gap-1 rounded-xl shadow-xs"
                    >
                      <Plus className="h-3.5 w-3.5" /> Add Banner
                    </Button>
                  </div>
                ) : (
                  featuredBanners.map((banner, index) => {
                    return (
                      <div
                        key={banner.id}
                        className="group relative p-3 rounded-xl border border-slate-200/80 bg-slate-50/70 hover:bg-slate-100/70 transition-all flex items-center justify-between gap-3"
                      >
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                          {/* Order arrangement controls (Up / Down arrows) */}
                          <div className="flex flex-col gap-0.5 flex-shrink-0">
                            <button
                              type="button"
                              disabled={index === 0}
                              onClick={(e) => handleMoveUp(index, e)}
                              className="p-0.5 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-800 disabled:opacity-20 disabled:hover:bg-transparent disabled:hover:text-slate-400 transition-colors"
                              title="Move Up in Order"
                            >
                              <ChevronUp className="h-3.5 w-3.5" />
                            </button>
                            <button
                              type="button"
                              disabled={index === featuredBanners.length - 1}
                              onClick={(e) => handleMoveDown(index, e)}
                              className="p-0.5 rounded hover:bg-slate-200 text-slate-400 hover:text-slate-800 disabled:opacity-20 disabled:hover:bg-transparent disabled:hover:text-slate-400 transition-colors"
                              title="Move Down in Order"
                            >
                              <ChevronDown className="h-3.5 w-3.5" />
                            </button>
                          </div>

                          {/* Video Banner Thumbnail */}
                          <div className="h-12 w-20 rounded-lg bg-slate-100 flex-shrink-0 overflow-hidden relative border border-slate-200 shadow-xs">
                            <img
                              src={banner.thumbnailUrl}
                              alt={banner.title}
                              className="w-full h-full object-cover"
                            />
                          </div>

                          {/* Banner Video Info */}
                          <div className="min-w-0 flex-1">
                            <h4 className="text-sm font-semibold text-slate-900 truncate">
                              {banner.title}
                            </h4>
                            <p className="text-xs text-slate-500 mt-0.5 truncate">
                              <span className="text-slate-700 font-medium">{banner.category}</span> · <span>{banner.duration}</span>
                            </p>
                          </div>
                        </div>

                        {/* Delete Banner Button */}
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button
                            type="button"
                            onClick={(e) => handleDeleteBanner(banner.id, banner.videoId, e)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                            title="Delete Banner"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </CardContent>
        </Card>
        </div>

        {/* Right Column: Sticky Mobile Preview */}
        <div className="xl:col-span-4 sticky top-6 z-10 w-full flex justify-center">
<div className="xl:col-span-5 flex flex-col items-center justify-center w-full">
  <div className="w-full max-w-[320px] space-y-3">
    <div className="flex items-center justify-between px-1">
      <span className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-2">
        <Smartphone className="h-4 w-4 text-slate-500" />
        Live Mobile Preview
      </span>
      <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-emerald-600">
        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
        Real-time
      </span>
    </div>

    {/* Phone Bezel Frame */}
    <div className="rounded-[44px] p-2.5 bg-slate-900 border-[6px] border-slate-800 shadow-2xl relative select-none">
      {/* Dynamic Island / Notch */}
      <div className="w-20 h-4 bg-black rounded-full mx-auto mb-2 shrink-0 flex items-center justify-end pr-2">
        <div className="w-2 h-2 rounded-full bg-slate-900 border border-slate-800" />
      </div>

      {/* Phone Screen Canvas */}
      <div
        className="rounded-[32px] overflow-hidden flex flex-col h-[520px] transition-all duration-300 relative border text-xs"
        style={{
          background: currentThemeAttributes.mainBackgroundColor,
          borderColor: currentThemeAttributes.mutedTextColor,
          color: currentThemeAttributes.primaryTextColor,
        }}
      >
        {/* Mobile Status Bar */}
        <div className="px-5 pt-1.5 pb-2 flex items-center justify-between text-[11px] font-semibold shrink-0" style={{ color: currentThemeAttributes.primaryTextColor }}>
          <span>9:41</span>
          <div className="flex items-center gap-1.5 opacity-90">
            <Signal className="h-3 w-3" />
            <Wifi className="h-3 w-3" />
            <Battery className="h-3.5 w-3.5" />
          </div>
        </div>

        {/* Mobile App Header */}
        <div
          className="px-4 py-2.5 flex items-center justify-between border-b shrink-0 transition-colors"
          style={{ borderColor: currentThemeAttributes.mutedTextColor }}
        >
          <div className="flex items-center gap-2 max-w-[170px]">
            {logoPreview ? (
              <img
                src={logoPreview}
                alt="Logo"
                className="h-6 w-auto max-w-[90px] object-contain"
              />
            ) : (
              <div className="h-6 w-6 rounded-md flex items-center justify-center font-bold text-xs" style={{ backgroundColor: currentThemeAttributes.primaryColor, color: currentThemeAttributes.buttonTextColor }}>
                {(studioName || creatorName || "S").charAt(0).toUpperCase()}
              </div>
            )}
            <span className="font-bold text-xs truncate" style={{ color: currentThemeAttributes.primaryTextColor }}>
              {studioName || creatorName || "TalentSea Studio"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5" style={{ color: currentThemeAttributes.secondaryTextColor }} />
            <Bell className="h-3.5 w-3.5" style={{ color: currentThemeAttributes.secondaryTextColor }} />
          </div>
        </div>

        {/* Scrollable Screen Content */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 no-scrollbar">
          {/* Featured Hero Banner */}
          <div
            className="rounded-xl overflow-hidden relative border shadow-sm group"
            style={{ borderColor: currentThemeAttributes.mutedTextColor }}
          >
            <div className="h-36 w-full relative">
              <img
                src={
                  featuredBanners[0]?.thumbnailUrl ||
                  bannerPreview ||
                  "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80"
                }
                alt="Featured Banner"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent" />

              {/* Accent Badge */}
              <div className="absolute top-2 left-2">
                <span
                  className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider shadow-xs"
                  style={{
                    backgroundColor: currentThemeAttributes.secondaryColor,
                    color: getContrastYIQ(currentThemeAttributes.secondaryColor),
                  }}
                >
                  PRO
                </span>
              </div>

              {/* Banner Overlay Info */}
              <div className="absolute bottom-2.5 left-2.5 right-2.5">
                <p className="text-[11px] font-bold text-white line-clamp-1 drop-shadow-sm">
                  {featuredBanners[0]?.title || "Cinematic Masterclass Vol. 1"}
                </p>
                <div className="flex items-center justify-between mt-1.5">
                  {/* Primary Brand Color Action Button */}
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[10px] font-bold shadow-xs transition-transform active:scale-95"
                    style={{
                      backgroundColor: currentThemeAttributes.primaryColor,
                      color: currentThemeAttributes.buttonTextColor,
                    }}
                  >
                    <Play className="h-2.5 w-2.5 fill-current" />
                    Watch Now
                  </button>
                  <span className="text-[9px] text-white/80 font-mono">
                    {featuredBanners[0]?.duration || "18:40"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Continue Watching Section */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span
                className="text-[10px] font-bold uppercase tracking-wider"
                style={{ color: currentThemeAttributes.secondaryTextColor }}
              >
                Continue Watching
              </span>
              <span className="text-[9px] font-medium" style={{ color: currentThemeAttributes.primaryColor }}>
                See All
              </span>
            </div>

            <div
              className="p-2 rounded-xl border flex items-center gap-2.5 transition-colors shadow-2xs"
              style={{
                backgroundColor: currentThemeAttributes.cardBackgroundColor,
                borderColor: currentThemeAttributes.mutedTextColor,
              }}
            >
              <div className="w-14 h-11 rounded-lg overflow-hidden relative shrink-0 bg-slate-800">
                <img
                  src="https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d?w=300&auto=format&fit=crop&q=80"
                  alt="Video thumb"
                  className="w-full h-full object-cover"
                />
                <div className="absolute bottom-0.5 right-0.5 bg-black/80 text-[8px] font-mono text-white px-1 rounded">
                  14:20
                </div>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <p className="text-[11px] font-semibold truncate" style={{ color: currentThemeAttributes.primaryTextColor }}>
                    Color Grading & LUTs
                  </p>
                      <span
                        className="text-[8px] font-bold px-1 py-0.2 rounded border shrink-0"
                        style={{
                          borderColor: currentThemeAttributes.secondaryColor,
                          color: currentThemeAttributes.secondaryColor,
                        }}
                      >
                        NEW
                      </span>
                    </div>

                    {/* Progress bar styled with Primary Brand Color */}
                    <div className="w-full h-1 rounded-full bg-slate-500/20 overflow-hidden mt-1.5">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: "65%",
                          backgroundColor: currentThemeAttributes.primaryColor,
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Secondary Video Mini Row */}
              <div className="space-y-2">
                <span
                  className="text-[10px] font-bold uppercase tracking-wider"
                  style={{ color: currentThemeAttributes.secondaryTextColor }}
                >
                  Latest Additions
                </span>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    {
                      title: "Lighting Setup 101",
                      tag: "HD",
                      img: "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?w=300&auto=format&fit=crop&q=80",
                    },
                    {
                      title: "Sound Design Pro",
                      tag: "4K",
                      img: "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=300&auto=format&fit=crop&q=80",
                    },
                  ].map((item, idx) => (
                    <div
                      key={idx}
                      className="p-1.5 rounded-xl border space-y-1.5"
                      style={{
                        backgroundColor: currentThemeAttributes.cardBackgroundColor,
                        borderColor: currentThemeAttributes.mutedTextColor,
                      }}
                    >
                      <div className="h-14 rounded-lg overflow-hidden relative bg-slate-800">
                        <img
                          src={item.img}
                          alt={item.title}
                          className="w-full h-full object-cover"
                        />
                        <span
                          className="absolute top-1 right-1 text-[8px] font-bold px-1 rounded"
                          style={{
                            backgroundColor: currentThemeAttributes.secondaryColor,
                            color: getContrastYIQ(currentThemeAttributes.secondaryColor),
                          }}
                        >
                          {item.tag}
                        </span>
                      </div>
                      <p className="text-[10px] font-semibold truncate px-0.5" style={{ color: currentThemeAttributes.primaryTextColor }}>
                        {item.title}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Mobile Bottom Navigation Bar */}
            <div
              className="px-4 py-2 border-t flex items-center justify-around shrink-0 transition-colors"
              style={{
                backgroundColor: currentThemeAttributes.cardBackgroundColor,
                borderColor: currentThemeAttributes.mutedTextColor,
              }}
            >
              {/* Active Home Tab */}
              <div className="flex flex-col items-center gap-0.5 cursor-pointer">
                <Home className="h-4 w-4" style={{ color: currentThemeAttributes.primaryColor }} />
                <span className="text-[8px] font-bold" style={{ color: currentThemeAttributes.primaryColor }}>
                  Home
                </span>
                <div
                  className="w-1 h-1 rounded-full"
                  style={{ backgroundColor: currentThemeAttributes.primaryColor }}
                />
              </div>

              {/* Inactive Tab: Explore */}
              <div className="flex flex-col items-center gap-0.5 opacity-60">
                <Compass className="h-4 w-4" style={{ color: currentThemeAttributes.secondaryTextColor }} />
                <span className="text-[8px]" style={{ color: currentThemeAttributes.secondaryTextColor }}>
                  Explore
                </span>
                <div className="w-1 h-1 opacity-0" />
              </div>

              {/* Inactive Tab: Library */}
              <div className="flex flex-col items-center gap-0.5 opacity-60">
                <Film className="h-4 w-4" style={{ color: currentThemeAttributes.secondaryTextColor }} />
                <span className="text-[8px]" style={{ color: currentThemeAttributes.secondaryTextColor }}>
                  Library
                </span>
                <div className="w-1 h-1 opacity-0" />
              </div>

              {/* Inactive Tab: Profile */}
              <div className="flex flex-col items-center gap-0.5 opacity-60">
                <User className="h-4 w-4" style={{ color: currentThemeAttributes.secondaryTextColor }} />
                <span className="text-[8px]" style={{ color: currentThemeAttributes.secondaryTextColor }}>
                  Profile
                </span>
                <div className="w-1 h-1 opacity-0" />
              </div>
            </div>
          </div>
        </div>

    <p className="text-center text-[11px] text-slate-400 font-medium">
      Changes reflect immediately in the mobile preview canvas.
    </p>
  </div>
</div>

        </div>
      </div>
    </div>
  );
}
