// API Service module for communicating with Content Management backend REST endpoints

function getBaseUrl(): string {
  const envUrl =
    (import.meta as any).env?.VITE_API_BASE_URL ||
    (import.meta as any).env?.VITE_BACKEND_API_URL ||
    (typeof window !== "undefined" && ((window as any).env?.VITE_API_BASE_URL || (window as any).env?.VITE_BACKEND_API_URL)) ||
    "";

  const trimmed = (envUrl || "").trim().replace(/\/+$/, "");

  // If page is loaded over HTTPS (e.g. Vercel deployment) and API URL is not secure HTTPS,
  // fallback to relative path ("") to route through Vercel /api reverse proxy and prevent Mixed Content blocking.
  if (typeof window !== "undefined" && window.location.protocol === "https:") {
    if (trimmed && !trimmed.startsWith("https://")) {
      console.warn(
        `[API Service] HTTPS page detected with non-HTTPS API URL ("${trimmed}"). Routing via relative proxy (/api) to prevent Mixed Content errors.`
      );
      return "";
    }
  }

  return trimmed;
}

const BASE_URL = getBaseUrl();

// ── Types & Interfaces ──────────────────────────────────────────────────────

export interface ApiVideo {
  id: number;
  title: string;
  description?: string;
  category?: string;
  status: string;
  views?: number | string;
  likes?: number;
  duration?: string;
  date?: string;
  publishedAt?: string;
  scheduledAt?: string;
  createdAt?: string;
  premium?: boolean;
  tags?: string[];
  thumbnailUrl?: string;
  mainThumbnailUrl?: string;
  altThumbnail1Url?: string;
  altThumbnail2Url?: string;
  altThumbnailUrls?: string[];
  bunnyVideoId?: string;
  playbackUrl?: string;
  videoUrl?: string;
  encodeProgress?: number;
  isPlayable?: boolean;
  captionsData?: Array<{ srclang?: string; label?: string; is_default?: boolean; isDefault?: boolean; url?: string }>;
  captionUrl?: string;
  captionSrclang?: string;
  captionLabel?: string;
  downloadUrls?: Array<{ resolution: string; label: string; url: string }>;
}

export interface ApiPlaylist {
  id: number;
  name: string;
  title: string;
  description?: string;
  videoCount?: number;
  videoIds?: number[];
  videos?: number;
  date?: string;
  createdAt?: string;
  updatedAt?: string;
  thumbnailUrl?: string;
}

export interface ApiComment {
  id: number;
  userId: number;
  userName: string;
  userAvatar?: string;
  text: string;
  videoId: number;
  videoTitle?: string;
  likes: number;
  isLiked: boolean;
  replyCount: number;
  createdAt: string;
}

export interface ApiReply {
  id: number;
  commentId: number;
  text: string;
  userId: number;
  userName: string;
  userAvatar?: string;
  isCreator?: boolean;
  likes?: number;
  isLiked?: boolean;
  replyCount?: number;
  createdAt: string;
}

export interface ApiSocialLinks {
  twitter?: string;
  youtube?: string;
  instagram?: string;
}

export interface ApiProfile {
  firstName: string;
  lastName: string;
  email: string;
  bio?: string;
  website?: string;
  phone?: string;
  location?: string;
  avatarUrl?: string;
  socialLinks?: ApiSocialLinks;
  updatedAt?: string;
}

export interface ApiFeaturedVideoItem {
  id: number;
  videoId: number;
  position: number;
  title: string;
  category?: string;
  thumbnailUrl: string;
  duration?: string;
  views?: number;
  likes?: number;
  status?: string;
  createdAt?: string;
}

export interface ApiAvailableFeaturedVideo {
  id: number;
  title: string;
  category?: string;
  duration?: string;
  thumbnailUrl: string;
  views?: number;
  likes?: number;
  createdAt?: string;
}

export interface ApiSubscriptionPlan {
  id: number;
  name: string;
  description?: string | null;
  base_price: number;
  discount_percentage: number;
  final_price: number;
  currency: string;
  billing_period_value: number;
  billing_period_unit: string;
  features: string[];
  badge_text?: string | null;
  is_active: boolean;
  display_order: number;
  active_subscribers: number;
  monthly_revenue: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateSubscriptionPlanPayload {
  name: string;
  base_price: number;
  discount_percentage: number;
  billing_period_value: number;
  billing_period_unit: string;
  description?: string | null;
  features: string[];
  badge_text?: string | null;
  is_active: boolean;
}

export interface UpdateSubscriptionPlanPayload {
  name?: string | null;
  base_price?: number | null;
  discount_percentage?: number | null;
  billing_period_value?: number | null;
  billing_period_unit?: string | null;
  description?: string | null;
  features?: string[] | null;
  badge_text?: string | null;
  is_active?: boolean | null;
}

// ── Internal Helpers ────────────────────────────────────────────────────────

function getAuthToken(): string {
  return (
    localStorage.getItem("access_token") ||
    (import.meta as any).env?.VITE_API_TOKEN ||
    (typeof window !== "undefined" && (window as any).env?.VITE_API_TOKEN) ||
    ""
  );
}

function getAuthHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${getAuthToken()}`,
  };
}

import { apiMonitorStore } from "./apiMonitorService";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    apiMonitorStore.addLog({
      url: response.url,
      method: "API",
      status: response.status,
      ok: false,
      data: { error: errorText || response.statusText },
    });
    throw new Error(`API Error ${response.status}: ${errorText || response.statusText}`);
  }
  const data = await response.json();
  apiMonitorStore.addLog({
    url: response.url,
    method: "API",
    status: response.status,
    ok: true,
    data: data,
  });
  return data;
}

function transformVideo(raw: any): ApiVideo {
  if (!raw) return raw;
  const bunnyId = raw.bunny_video_id || raw.bunnyVideoId;
  const directPlayback = raw.playback_url || raw.playbackUrl || raw.video_url || raw.videoUrl || raw.url;

  const altUrls = Array.isArray(raw.alt_thumbnail_urls)
    ? raw.alt_thumbnail_urls
    : Array.isArray(raw.altThumbnailUrls)
      ? raw.altThumbnailUrls
      : [raw.alt_thumbnail_1_url, raw.alt_thumbnail_2_url].filter(Boolean);

  const captions = Array.isArray(raw.captions_data)
    ? raw.captions_data
    : Array.isArray(raw.captionsData)
      ? raw.captionsData
      : Array.isArray(raw.captions)
        ? raw.captions
        : [];

  const primaryCaption = captions.find((c: any) => c.is_default || c.isDefault) || captions[0];
  const fetchedCaptionUrl = primaryCaption?.url || raw.caption_url || raw.captionUrl || undefined;
  const fetchedCaptionSrclang = primaryCaption?.srclang || primaryCaption?.srcLang || raw.caption_srclang || undefined;
  const fetchedCaptionLabel = primaryCaption?.label || raw.caption_label || undefined;

  const downloadUrls = Array.isArray(raw.download_urls)
    ? raw.download_urls
    : Array.isArray(raw.downloadUrls)
      ? raw.downloadUrls
      : [];

  return {
    id: raw.id ?? raw.video_id,
    title: raw.title || "Untitled Video",
    description: raw.description || "",
    category: raw.category || "Uncategorized",
    status: raw.status ? String(raw.status) : "draft",
    views: raw.views_count ?? raw.views ?? 0,
    likes: raw.likes_count ?? raw.likes ?? 0,
    duration: raw.duration || "0:00",
    date: raw.created_at ? raw.created_at.split("T")[0] : raw.date || new Date().toISOString().split("T")[0],
    publishedAt: raw.published_at || raw.publishedAt,
    scheduledAt: raw.scheduled_at || raw.scheduledAt,
    createdAt: raw.created_at || raw.createdAt,
    premium: raw.is_premium ?? raw.premium ?? false,
    tags: Array.isArray(raw.tags) ? raw.tags : typeof raw.tags === "string" ? JSON.parse(raw.tags) : [],
    thumbnailUrl: raw.main_thumbnail_url || raw.thumbnailUrl || raw.thumbnail,
    mainThumbnailUrl: raw.main_thumbnail_url || raw.mainThumbnailUrl,
    altThumbnail1Url: altUrls[0] || raw.alt_thumbnail_1_url || raw.altThumbnail1Url,
    altThumbnail2Url: altUrls[1] || raw.alt_thumbnail_2_url || raw.altThumbnail2Url,
    altThumbnailUrls: altUrls,
    bunnyVideoId: bunnyId,
    playbackUrl: directPlayback,
    videoUrl: directPlayback,
    encodeProgress: raw.encode_progress ?? raw.encodeProgress ?? (raw.encode_progress === 0 ? 0 : raw.is_playable === false ? 65 : undefined),
    isPlayable: raw.is_playable ?? raw.isPlayable ?? true,
    captionsData: captions,
    captionUrl: fetchedCaptionUrl,
    captionSrclang: fetchedCaptionSrclang,
    captionLabel: fetchedCaptionLabel,
    downloadUrls: downloadUrls,
  };
}

function transformPlaylist(raw: any): ApiPlaylist {
  if (!raw) return raw;
  const nameVal = raw.name || raw.title || "Untitled Playlist";
  const descVal = raw.description || raw.desc || raw.summary || raw.details || "";
  return {
    id: raw.id ?? raw.playlist_id,
    name: nameVal,
    title: nameVal,
    description: descVal,
    videoCount: raw.video_count ?? raw.videoCount ?? (raw.video_ids ? raw.video_ids.length : 0),
    videos: raw.video_count ?? raw.videoCount ?? (raw.video_ids ? raw.video_ids.length : 0),
    videoIds: raw.video_ids || raw.videoIds || [],
    date: raw.created_at ? raw.created_at.split("T")[0] : raw.date || new Date().toISOString().split("T")[0],
    createdAt: raw.created_at || raw.createdAt,
    updatedAt: raw.updated_at || raw.updatedAt,
    thumbnailUrl: raw.thumbnail_url || raw.banner_image_url || raw.thumbnailUrl || raw.thumbnail,
  };
}

function transformComment(raw: any): ApiComment {
  const author = raw.author || {};
  return {
    id: raw.id,
    userId: author.id ?? raw.user_id ?? raw.userId ?? 0,
    userName: author.name || raw.user_name || raw.userName || "User",
    userAvatar: author.avatar_url || author.avatarUrl || raw.user_avatar || raw.userAvatar,
    text: raw.text || "",
    videoId: raw.video_id ?? raw.videoId ?? 0,
    videoTitle: raw.video_title || raw.videoTitle || "",
    likes: raw.likes ?? 0,
    isLiked: raw.is_liked ?? raw.isLiked ?? false,
    replyCount: raw.reply_count ?? raw.replyCount ?? 0,
    createdAt: raw.created_at || raw.createdAt || new Date().toISOString(),
  };
}

function transformReply(raw: any): ApiReply {
  const author = raw.author || {};
  return {
    id: raw.id,
    commentId: raw.comment_id ?? raw.commentId ?? 0,
    text: raw.text || "",
    userId: author.id ?? raw.user_id ?? raw.userId ?? 0,
    userName: author.name || raw.user_name || raw.userName || "User",
    userAvatar: author.avatar_url || author.avatarUrl || raw.user_avatar || raw.userAvatar,
    isCreator: author.is_creator ?? author.isCreator ?? raw.is_creator ?? false,
    likes: raw.likes_count ?? raw.likesCount ?? raw.likes ?? 0,
    isLiked: raw.is_liked ?? raw.isLiked ?? false,
    replyCount: raw.reply_count ?? raw.replyCount ?? raw.replies_count ?? 0,
    createdAt: raw.created_at || raw.createdAt || new Date().toISOString(),
  };
}

function transformProfile(raw: any): ApiProfile {
  return {
    firstName: raw.first_name || raw.firstName || "",
    lastName: raw.last_name || raw.lastName || "",
    email: raw.email || "",
    bio: raw.bio || "",
    website: raw.website || "",
    phone: raw.phone || "",
    location: raw.location || "",
    avatarUrl: raw.avatar_url || raw.avatarUrl || "",
    socialLinks: {
      twitter: raw.social_links?.twitter || raw.socialLinks?.twitter || "",
      youtube: raw.social_links?.youtube || raw.socialLinks?.youtube || "",
      instagram: raw.social_links?.instagram || raw.socialLinks?.instagram || "",
    },
    updatedAt: raw.updated_at || raw.updatedAt,
  };
}

// ── Videos API ─────────────────────────────────────────────────────────────

export async function getVideos(params?: {
  status?: string;
  category?: string;
  search?: string;
  sort?: string;
  dateFrom?: string;
  dateTo?: string;
  page?: number;
  limit?: number;
}): Promise<{ data: ApiVideo[]; pagination?: any }> {
  try {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.category) query.append("category", params.category);
    if (params?.search) query.append("search", params.search);
    if (params?.sort) query.append("sort", params.sort);
    if (params?.dateFrom) query.append("dateFrom", params.dateFrom);
    if (params?.dateTo) query.append("dateTo", params.dateTo);
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());

    const res = await fetch(`${BASE_URL}/api/v1/admin/videos?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<any>(res);
    return {
      data: (json.data || json.items || json || []).map(transformVideo),
      pagination: {
        total: json.total ?? json.pagination?.total ?? 0,
        page: json.page ?? json.pagination?.page ?? 1,
        limit: json.limit ?? json.pagination?.limit ?? 20,
        totalPages: json.total_pages ?? json.pagination?.totalPages ?? 1,
      },
    };
  } catch (err) {
    console.warn("Video API request failed", err);
    throw err;
  }
}

export async function getVideoDetails(id: number): Promise<ApiVideo> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${id}`, {
    headers: getAuthHeaders(),
  });
  const json = await handleResponse<any>(res);
  return transformVideo(json);
}

export async function initiateVideoUpload(data: {
  title: string;
  description?: string;
  category?: string;
  tags?: string[];
  status?: string;
  filename?: string;
}): Promise<{
  id: number;
  bunnyVideoId?: string;
  bunnyLibraryId?: string;
  uploadUrl?: string;
  signature?: string;
  expirationTime?: number;
  status?: string;
  encodeProgress?: number;
}> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/initiate`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      title: data.title,
      description: data.description,
      category: data.category,
      tags: data.tags || [],
      status: data.status || "draft",
    }),
  });
  const json = await handleResponse<any>(res);
  return {
    id: json.id || json.video_id,
    bunnyVideoId: json.bunny_video_id || json.bunnyVideoId,
    bunnyLibraryId: json.bunny_library_id || json.bunnyLibraryId,
    uploadUrl: json.upload_url || json.uploadUrl,
    signature: json.signature,
    expirationTime: json.expiration_time || json.expirationTime,
    status: json.status,
    encodeProgress: json.encode_progress ?? json.encodeProgress ?? 0,
  };
}

export async function updateVideo(
  id: number,
  data: Partial<ApiVideo>
): Promise<ApiVideo> {
  const payload: any = {};
  if (data.title !== undefined) payload.title = data.title;
  if (data.description !== undefined) payload.description = data.description;
  if (data.category !== undefined) payload.category = data.category;
  if (data.tags !== undefined) payload.tags = data.tags;
  if (data.premium !== undefined) payload.is_premium = data.premium;

  try {
    const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${id}`, {
      method: "PATCH",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const json = await handleResponse<any>(res);
    return transformVideo(json);
  } catch (err: any) {
    try {
      const updated = await getVideoDetails(id);
      return updated;
    } catch {
      throw err;
    }
  }
}

export async function deleteVideo(id: number): Promise<{ success: boolean; message?: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function bulkDeleteVideos(videoIds: number[]): Promise<{ status?: string; success?: boolean }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/bulk-delete`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_ids: videoIds }),
  });
  return handleResponse(res);
}

export async function publishVideo(id: number): Promise<ApiVideo> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${id}/publish`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const json = await handleResponse<any>(res);
  return transformVideo(json);
}

export async function scheduleVideo(
  id: number,
  schedule: { date: string; time: string }
): Promise<ApiVideo> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${id}/schedule`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      date: schedule.date,
      time: schedule.time,
    }),
  });
  const json = await handleResponse<any>(res);
  return transformVideo(json);
}

export async function uploadThumbnail(
  videoId: number,
  slot: number,
  file: File
): Promise<{ status?: string; success?: boolean }> {
  const formData = new FormData();
  formData.append("file", file);

  const token = getAuthToken();
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${videoId}/thumbnails/upload?slot=${slot}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  return handleResponse(res);
}

export async function selectMainThumbnail(
  videoId: number,
  slotOrUrl: number | string
): Promise<{ status?: string; success?: boolean }> {
  const payload = typeof slotOrUrl === "string"
    ? { selected_main_thumbnail: slotOrUrl }
    : { selected_main_thumbnail: String(slotOrUrl), slot: slotOrUrl };
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${videoId}/thumbnails/select-main`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function deleteThumbnail(
  videoId: number,
  slotOrUrl?: number | string
): Promise<{ status?: string; success?: boolean }> {
  const payload = typeof slotOrUrl === "string"
    ? { thumbnail_url: slotOrUrl }
    : slotOrUrl !== undefined
      ? { thumbnail_url: String(slotOrUrl), slot: slotOrUrl }
      : { thumbnail_url: "" };
  const res = await fetch(`${BASE_URL}/api/v1/admin/videos/${videoId}/thumbnails`, {
    method: "DELETE",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

// ── Branding API ────────────────────────────────────────────────────────────

export interface ApiBranding {
  creatorName: string;
  tagline: string;
  description: string;
  bannerUrl: string;
  logoUrl: string;
  updatedAt?: string;
}

function transformBranding(raw: any): ApiBranding {
  if (!raw) return { creatorName: "", tagline: "", description: "", bannerUrl: "", logoUrl: "" };
  return {
    creatorName: raw.creator_name || raw.creatorName || "",
    tagline: raw.tagline || "",
    description: raw.description || "",
    bannerUrl: raw.banner_url || raw.bannerUrl || "",
    logoUrl: raw.logo_url || raw.logoUrl || "",
    updatedAt: raw.updated_at || raw.updatedAt,
  };
}

export async function getCreatorBranding(): Promise<ApiBranding> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/admin/branding`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<any>(res);
    return transformBranding(json);
  } catch (err) {
    console.warn("Branding API request failed", err);
    throw err;
  }
}

export async function updateCreatorBranding(data: {
  creator_name?: string;
  creatorName?: string;
  tagline?: string;
  description?: string;
}): Promise<ApiBranding> {
  const payload: any = {};
  if (data.creator_name !== undefined) payload.creator_name = data.creator_name;
  else if (data.creatorName !== undefined) payload.creator_name = data.creatorName;
  if (data.tagline !== undefined) payload.tagline = data.tagline;
  if (data.description !== undefined) payload.description = data.description;

  const res = await fetch(`${BASE_URL}/api/v1/admin/branding`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  const json = await handleResponse<any>(res);
  return transformBranding(json);
}

export async function uploadCreatorLogo(file: File): Promise<{ logoUrl: string }> {
  const formData = new FormData();
  formData.append("logo", file);

  const token = getAuthToken();
  const res = await fetch(`${BASE_URL}/api/v1/admin/branding/logo`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const json = await handleResponse<any>(res);
  return {
    logoUrl: json.logo_url || json.logoUrl || "",
  };
}

export async function uploadCreatorBanner(file: File): Promise<{ bannerUrl: string }> {
  const formData = new FormData();
  formData.append("banner", file);

  const token = getAuthToken();
  const res = await fetch(`${BASE_URL}/api/v1/admin/branding/banner`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const json = await handleResponse<any>(res);
  return {
    bannerUrl: json.banner_url || json.bannerUrl || "",
  };
}

// ── Featured Videos API ────────────────────────────────────────────────────

export async function getFeaturedVideos(): Promise<ApiFeaturedVideoItem[]> {
  try {
    let res = await fetch(`${BASE_URL}/api/v1/admin/featured-videos`, {
      headers: getAuthHeaders(),
    });
    if (res.status === 404) {
      res = await fetch(`${BASE_URL}/featured-videos`, {
        headers: getAuthHeaders(),
      });
    }
    const json = await handleResponse<any[]>(res);
    return (json || []).map((raw: any) => ({
      id: raw.id,
      videoId: raw.video_id ?? raw.videoId ?? raw.id,
      position: raw.position ?? 1,
      title: raw.title || "",
      category: raw.category || "General",
      thumbnailUrl: raw.main_thumbnail_url || raw.thumbnail_url || raw.thumbnailUrl || "",
      duration: raw.duration || "00:00",
      views: raw.views ?? 0,
      likes: raw.likes ?? 0,
      status: raw.status || "published",
      createdAt: raw.created_at || raw.createdAt,
    }));
  } catch (err) {
    console.warn("Failed to fetch featured videos from API", err);
    throw err;
  }
}

export async function updateFeaturedVideos(videoIds: number[]): Promise<boolean> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/featured-videos`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/featured-videos`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }

  if (res.ok) {
    await handleResponse<any>(res);
    return true;
  }

  // Fallback if PUT full state sync endpoint is not enabled: try POST + PUT /reorder
  if (res.status === 405 || res.status === 404) {
    if (videoIds.length > 0) {
      await addFeaturedVideos(videoIds);
      await reorderFeaturedVideos(videoIds);
    } else {
      try {
        await bulkDeleteFeaturedVideos([]);
      } catch (_) {}
    }
    return true;
  }

  await handleResponse<any>(res);
  return true;
}

export const saveFeaturedVideos = updateFeaturedVideos;

export async function addFeaturedVideos(videoIds: number[]): Promise<{ addedCount: number; totalFeatured: number }> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/featured-videos`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/featured-videos`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }
  const json = await handleResponse<any>(res);
  return {
    addedCount: json.added_count ?? videoIds.length,
    totalFeatured: json.total_featured ?? 0,
  };
}

export async function reorderFeaturedVideos(videoIds: number[]): Promise<boolean> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/featured-videos/reorder`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/featured-videos/reorder`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }
  await handleResponse<any>(res);
  return true;
}

export async function deleteFeaturedVideo(videoId: number): Promise<boolean> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/featured-videos/${videoId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/featured-videos/${videoId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
  }
  await handleResponse<any>(res);
  return true;
}

export async function bulkDeleteFeaturedVideos(videoIds: number[]): Promise<boolean> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/featured-videos`, {
    method: "DELETE",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/featured-videos`, {
      method: "DELETE",
      headers: getAuthHeaders(),
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }
  await handleResponse<any>(res);
  return true;
}

export async function getAvailableVideosForFeatured(params?: {
  search?: string;
  category?: string;
  sort?: string;
  page?: number;
  limit?: number;
}): Promise<{ items: ApiAvailableFeaturedVideo[]; total: number }> {
  try {
    const query = new URLSearchParams();
    if (params?.search) query.append("search", params.search);
    if (params?.category) query.append("category", params.category);
    if (params?.sort) query.append("sort", params.sort);
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());

    let res = await fetch(`${BASE_URL}/api/v1/admin/featured-videos/available?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (res.status === 404) {
      res = await fetch(`${BASE_URL}/featured-videos/available?${query.toString()}`, {
        headers: getAuthHeaders(),
      });
    }
    if (res.ok) {
      const json = await handleResponse<any>(res);
      const itemsRaw = json.items || json.data || (Array.isArray(json) ? json : []);
      if (Array.isArray(itemsRaw) && itemsRaw.length > 0) {
        const items: ApiAvailableFeaturedVideo[] = itemsRaw.map((raw: any) => ({
          id: raw.id,
          title: raw.title || "",
          category: raw.category || "General",
          duration: raw.duration || "00:00",
          thumbnailUrl: raw.main_thumbnail_url || raw.thumbnail_url || raw.thumbnailUrl || "",
          views: typeof raw.views === "number" ? raw.views : parseInt(String(raw.views || 0), 10) || 0,
          likes: typeof raw.likes === "number" ? raw.likes : parseInt(String(raw.likes || 0), 10) || 0,
          createdAt: raw.created_at || raw.createdAt,
        }));
        return { items, total: json.total ?? items.length };
      }
    }
  } catch (err) {
    console.warn("Featured-videos/available endpoint fallback to /admin/videos:", err);
  }

  // Fallback to getVideos() -> GET /api/v1/admin/videos
  try {
    const videosRes = await getVideos({ search: params?.search, category: params?.category, sort: params?.sort });
    const items: ApiAvailableFeaturedVideo[] = (videosRes.data || []).map((v) => ({
      id: v.id,
      title: v.title || "",
      category: v.category || "General",
      duration: v.duration || "00:00",
      thumbnailUrl: v.thumbnailUrl || v.mainThumbnailUrl || "",
      views: typeof v.views === "number" ? v.views : parseInt(String(v.views || 0), 10) || 0,
      likes: v.likes ?? 0,
      createdAt: v.createdAt,
    }));
    return { items, total: items.length };
  } catch (err) {
    console.warn("Failed to fetch available videos fallback:", err);
    return { items: [], total: 0 };
  }
}

// ── Playlists API ──────────────────────────────────────────────────────────

export async function getPlaylists(params?: {
  search?: string;
  sort?: string;
  page?: number;
  limit?: number;
}): Promise<{ data: ApiPlaylist[]; pagination?: any }> {
  try {
    const query = new URLSearchParams();
    if (params?.search) query.append("search", params.search);
    if (params?.sort) query.append("sort", params.sort);
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());

    let res = await fetch(`${BASE_URL}/api/v1/admin/playlists?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    if (res.status === 404) {
      res = await fetch(`${BASE_URL}/playlists?${query.toString()}`, {
        headers: getAuthHeaders(),
      });
    }
    const json = await handleResponse<any>(res);
    const rawList = Array.isArray(json) ? json : (json.data || json.items || []);

    const playlists: ApiPlaylist[] = (Array.isArray(rawList) ? rawList : []).map(transformPlaylist);

    return {
      data: playlists,
      pagination: {
        total: json.total ?? json.pagination?.total ?? playlists.length,
        page: json.page ?? json.pagination?.page ?? 1,
        limit: json.limit ?? json.pagination?.limit ?? 20,
        totalPages: json.total_pages ?? json.pagination?.totalPages ?? 1,
      },
    };
  } catch (err) {
    console.warn("Playlist API request failed", err);
    throw err;
  }
}

export async function getPlaylistDetails(id: number): Promise<ApiPlaylist> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${id}`, {
    headers: getAuthHeaders(),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${id}`, {
      headers: getAuthHeaders(),
    });
  }
  const json = await handleResponse<any>(res);
  return transformPlaylist(json);
}


export async function createPlaylist(data: {
  name?: string;
  title?: string;
  description?: string;
  videoIds?: number[];
  video_ids?: number[];
}): Promise<ApiPlaylist> {
  const nameVal = data.name || data.title || "Untitled Playlist";
  const descVal = data.description || "";
  const videoIds = data.video_ids || data.videoIds || [];

  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      name: nameVal,
      description: descVal,
      video_ids: videoIds,
    }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        name: nameVal,
        description: descVal,
        video_ids: videoIds,
      }),
    });
  }
  const json = await handleResponse<any>(res);
  return transformPlaylist(json);
}

export async function updatePlaylist(
  id: number,
  data: { name?: string; title?: string; description?: string }
): Promise<ApiPlaylist> {
  const nameVal = data.name || data.title || "";
  const descVal = data.description;
  const payload: any = {};
  if (nameVal) payload.name = nameVal;
  if (descVal !== undefined) payload.description = descVal;

  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${id}`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    });
  }
  const json = await handleResponse<any>(res);
  return transformPlaylist(json);
}

export async function deletePlaylist(id: number): Promise<{ status?: string; success?: boolean }> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${id}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });
  }
  return handleResponse(res);
}

export async function uploadPlaylistBanner(
  playlistId: number,
  file: File
): Promise<{ status?: string; success?: boolean }> {
  const formData = new FormData();
  formData.append("file", file);

  const token = getAuthToken();
  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/thumbnail/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${playlistId}/thumbnail/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
  }
  return handleResponse(res);
}

export async function getPlaylistVideos(
  playlistId: number,
  params?: { search?: string; page?: number; limit?: number }
): Promise<{ data: ApiVideo[]; pagination?: any }> {
  const query = new URLSearchParams();
  if (params?.search) query.append("search", params.search);
  if (params?.page) query.append("page", params.page.toString());
  if (params?.limit) query.append("limit", params.limit.toString());

  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${playlistId}/videos?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
  }
  const json = await handleResponse<any>(res);
  return {
    data: (json.data || json.items || json || []).map(transformVideo),
    pagination: {
      total: json.total ?? json.pagination?.total ?? 0,
      page: json.page ?? json.pagination?.page ?? 1,
      limit: json.limit ?? json.pagination?.limit ?? 20,
      totalPages: json.total_pages ?? json.pagination?.totalPages ?? 1,
    },
  };
}

export async function addVideosToPlaylist(
  playlistId: number,
  videoIds: number[]
): Promise<{ status?: string; success?: boolean }> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${playlistId}/videos`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }
  return handleResponse(res);
}

export async function removeVideoFromPlaylist(
  playlistId: number,
  videoId: number
): Promise<{ status?: string; success?: boolean }> {
  let res = await fetch(
    `${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos/${videoId}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    }
  );
  if (res.status === 404) {
    res = await fetch(
      `${BASE_URL}/playlists/${playlistId}/videos/${videoId}`,
      {
        method: "DELETE",
        headers: getAuthHeaders(),
      }
    );
  }
  return handleResponse(res);
}

export async function bulkRemoveVideosFromPlaylist(
  playlistId: number,
  videoIds: number[]
): Promise<{ status?: string; success?: boolean }> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos`, {
    method: "DELETE",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${playlistId}/videos`, {
      method: "DELETE",
      headers: getAuthHeaders(),
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }
  return handleResponse(res);
}

export async function getAvailableVideosForPlaylist(
  playlistId: number,
  params?: { search?: string; category?: string; sort?: string; page?: number; limit?: number }
): Promise<{ data: ApiVideo[]; pagination?: any }> {
  const query = new URLSearchParams();
  if (params?.search) query.append("search", params.search);
  if (params?.category) query.append("category", params.category);
  if (params?.sort) query.append("sort", params.sort);
  if (params?.page) query.append("page", params.page.toString());
  if (params?.limit) query.append("limit", params.limit.toString());

  let res = await fetch(
    `${BASE_URL}/api/v1/admin/playlists/${playlistId}/available_videos?${query.toString()}`,
    { headers: getAuthHeaders() }
  );
  if (res.status === 404) {
    res = await fetch(
      `${BASE_URL}/playlists/${playlistId}/available_videos?${query.toString()}`,
      { headers: getAuthHeaders() }
    );
  }
  const json = await handleResponse<any>(res);
  return {
    data: (json.data || json.items || json || []).map(transformVideo),
    pagination: {
      total: json.total ?? json.pagination?.total ?? 0,
      page: json.page ?? json.pagination?.page ?? 1,
      limit: json.limit ?? json.pagination?.limit ?? 20,
      totalPages: json.total_pages ?? json.pagination?.totalPages ?? 1,
    },
  };
}

export async function reorderPlaylistVideos(
  playlistId: number,
  videoOrders: { video_id: number; order: number }[]
): Promise<{ status?: string; success?: boolean }> {
  let res = await fetch(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos/reorder`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({ video_orders: videoOrders }),
  });
  if (res.status === 404) {
    res = await fetch(`${BASE_URL}/playlists/${playlistId}/videos/reorder`, {
      method: "PUT",
      headers: getAuthHeaders(),
      body: JSON.stringify({ video_orders: videoOrders }),
    });
  }
  return handleResponse(res);
}

// ── Comments API ───────────────────────────────────────────────────────────

export async function getAdminComments(params?: {
  category?: string;
  videoId?: number;
  date?: string;
  minLikes?: number;
  search?: string;
  sort?: string;
  page?: number;
  limit?: number;
}): Promise<{ data: ApiComment[]; pagination?: any }> {
  try {
    const query = new URLSearchParams();
    if (params?.category) query.append("category", params.category);
    if (params?.videoId) query.append("videoId", params.videoId.toString());
    if (params?.date) query.append("date", params.date);
    if (params?.minLikes) query.append("minLikes", params.minLikes.toString());
    if (params?.search) query.append("search", params.search);
    if (params?.sort) query.append("sort", params.sort);
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());

    const res = await fetch(`${BASE_URL}/api/v1/admin/comments?${query.toString()}`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<any>(res);
    return {
      data: (json.data || json.items || json || []).map(transformComment),
      pagination: {
        total: json.total ?? json.pagination?.total ?? 0,
        page: json.page ?? json.pagination?.page ?? 1,
        limit: json.limit ?? json.pagination?.limit ?? 20,
        totalPages: json.total_pages ?? json.pagination?.totalPages ?? 1,
      },
    };
  } catch (err) {
    console.warn("Comments API request failed", err);
    throw err;
  }
}

export async function postAdminVideoComment(
  videoId: number,
  text: string
): Promise<ApiComment> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/comments/videos/${videoId}/comments`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ text }),
  });
  const json = await handleResponse<any>(res);
  return transformComment(json);
}

export async function getCommentReplies(
  commentId: number,
  params?: { sort?: string; page?: number; limit?: number }
): Promise<{ data: ApiReply[]; pagination?: any }> {
  const query = new URLSearchParams();
  if (params?.sort) query.append("sort", params.sort);
  if (params?.page) query.append("page", params.page.toString());
  if (params?.limit) query.append("limit", params.limit.toString());

  const res = await fetch(
    `${BASE_URL}/api/v1/admin/comments/${commentId}/replies?${query.toString()}`,
    { headers: getAuthHeaders() }
  );
  const json = await handleResponse<any>(res);
  return {
    data: (json.data || json.items || json || []).map(transformReply),
    pagination: {
      total: json.total ?? json.pagination?.total ?? 0,
      page: json.page ?? json.pagination?.page ?? 1,
      limit: json.limit ?? json.pagination?.limit ?? 20,
      totalPages: json.total_pages ?? json.pagination?.totalPages ?? 1,
    },
  };
}

export async function postCommentReply(
  commentId: number,
  text: string
): Promise<ApiReply> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/comments/${commentId}/reply`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ text }),
  });
  const json = await handleResponse<any>(res);
  return transformReply(json);
}

export async function toggleCommentLike(
  commentId: number
): Promise<{ status: string; isLiked: boolean; likes: number }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/comments/${commentId}/like`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  const json = await handleResponse<any>(res);
  return {
    status: json.status || "success",
    isLiked: json.is_liked ?? json.isLiked ?? false,
    likes: json.likes ?? 0,
  };
}

export async function deleteComment(
  commentId: number
): Promise<{ status?: string; success?: boolean }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/comments/${commentId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

// ── Settings / Profile API ─────────────────────────────────────────────────

export async function getCreatorProfile(): Promise<ApiProfile> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/admin/profile`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<any>(res);
    return transformProfile(json);
  } catch (err) {
    console.warn("Profile API request failed", err);
    throw err;
  }
}

export async function updateCreatorProfile(
  data: Partial<{
    first_name: string;
    last_name: string;
    bio: string;
    website: string;
    phone: string;
    location: string;
    social_links: ApiSocialLinks;
  }>
): Promise<{ status?: string; success?: boolean }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/profile`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function uploadAvatarPhoto(
  file: File
): Promise<{ avatarUrl: string }> {
  const formData = new FormData();
  formData.append("photo", file);

  const token = getAuthToken();
  const res = await fetch(`${BASE_URL}/api/v1/admin/profile/photo`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const json = await handleResponse<any>(res);
  return {
    avatarUrl: json.avatar_url || json.avatarUrl || "",
  };
}

export interface ApiSubscriber {
  id: number;
  name: string;
  email: string;
  plan: string;
  status: string;
  joinDate: string;
  revenue: string;
}

export async function getSubscribers(params?: {
  filter?: "all" | "subscribers" | "users";
  limit?: number;
}): Promise<ApiSubscriber[]> {
  try {
    const res = await getDashboardRecentActivity({
      filter: params?.filter || "all",
      limit: params?.limit ? Math.min(params.limit, 20) : 20,
    });
    const items = Array.isArray(res) ? res : (res?.items || []);
    if (items.length > 0) {
      return items.map((item) => ({
        id: item.id,
        name: item.name || (item.email ? item.email.split("@")[0] : `User #${item.id}`),
        email: item.email || "No email (Phone/OAuth)",
        plan: item.planName || (item.isPaid ? "Paid Plan" : "Free"),
        status: item.isPaid ? "Active" : "Free",
        joinDate: item.joinedAt ? item.joinedAt.split("T")[0] : new Date().toISOString().split("T")[0],
        revenue: item.isPaid ? "₹499" : "₹0",
        avatarUrl: item.avatarUrl || undefined,
      }));
    }
  } catch (err) {
    console.warn("Failed to load subscribers from backend:", err);
  }
  return [];
}


// ── Categories Management API ──────────────────────────────────────────────

export interface ApiCategory {
  id: number;
  name: string;
  slug: string;
  description: string;
  icon: string;
  color: string;
  contentCount: number;
  order: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateCategoryPayload {
  name: string;
  description?: string;
  icon?: string;
  color?: string;
}

export interface UpdateCategoryPayload {
  name?: string;
  description?: string;
  icon?: string;
  color?: string;
}

function transformCategory(raw: any): ApiCategory {
  return {
    id: raw.id,
    name: raw.name || "Untitled Category",
    slug: raw.slug || "",
    description: raw.description || "",
    icon: raw.icon || "📁",
    color: raw.color || "#3b82f6",
    contentCount: raw.contentCount ?? raw.content_count ?? 0,
    order: raw.order ?? raw.display_order ?? 0,
    createdAt: raw.createdAt || raw.created_at || "",
    updatedAt: raw.updatedAt || raw.updated_at || "",
  };
}

export async function getCategories(params?: { simple?: boolean }): Promise<ApiCategory[]> {
  try {
    const query = new URLSearchParams();
    if (params?.simple) query.append("simple", "true");
    const queryString = query.toString();
    const url = queryString
      ? `${BASE_URL}/api/v1/admin/categories?${queryString}`
      : `${BASE_URL}/api/v1/admin/categories`;

    const res = await fetch(url, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<any>(res);
    const list = json.data || json.items || (Array.isArray(json) ? json : []);
    return list.map(transformCategory);
  } catch (err) {
    console.warn("Categories API request failed", err);
    throw err;
  }
}

export async function createCategory(data: CreateCategoryPayload): Promise<ApiCategory> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/categories`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  const json = await handleResponse<any>(res);
  return transformCategory(json);
}

export async function updateCategory(id: number, data: UpdateCategoryPayload): Promise<ApiCategory> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/categories/${id}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  const json = await handleResponse<any>(res);
  return transformCategory(json);
}

export async function deleteCategory(id: number): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/categories/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function reorderCategories(ids: number[]): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/categories/reorder`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({ ids }),
  });
  return handleResponse(res);
}

// ── Subscription Plans API Endpoints ────────────────────────────────────────

export async function getSubscriptionPlans(): Promise<ApiSubscriptionPlan[]> {
  try {
    const res = await fetch(`${BASE_URL}/api/v1/admin/plans`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<any>(res);
    return Array.isArray(json) ? json : json.data || json.items || [];
  } catch (err) {
    console.warn("[API Service] Subscription Plans API request failed", err);
    throw err;
  }
}

export async function createSubscriptionPlan(data: CreateSubscriptionPlanPayload): Promise<ApiSubscriptionPlan> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/plans`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<ApiSubscriptionPlan>(res);
}

export async function updateSubscriptionPlan(
  planId: number,
  data: UpdateSubscriptionPlanPayload
): Promise<ApiSubscriptionPlan> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/plans/${planId}`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<ApiSubscriptionPlan>(res);
}

export async function deleteSubscriptionPlan(planId: number): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/plans/${planId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function toggleSubscriptionPlanActive(
  planId: number
): Promise<{ id: number; name: string; is_active: boolean; updated_at: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/plans/${planId}/toggle-active`, {
    method: "PATCH",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function reorderSubscriptionPlans(ids: number[]): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/api/v1/admin/plans/reorder`, {
    method: "PUT",
    headers: getAuthHeaders(),
    body: JSON.stringify({ ids }),
  });
  return handleResponse(res);
}

// ── Dashboard & Analytics API Endpoints ─────────────────────────────────────

export interface GrowthMetric {
  current: number;
  previous: number;
  growth_percentage: number;
}

export interface ContentInventoryBreakdown {
  total: number;
  published: number;
  drafts: number;
  recently_added: number;
}

export interface ApiDashboardStats {
  startDate: string;
  endDate: string;
  currency: string;
  totalRevenue: GrowthMetric;
  totalViews: GrowthMetric;
  totalUsers: GrowthMetric;
  totalSubscribers: GrowthMetric;
  totalContent: ContentInventoryBreakdown;
}

export interface ApiAnalyticsDataPoint {
  date: string;
  label: string;
  users: number;
  subscribers: number;
  revenue: number;
  views: number;
}

export interface ApiAnalytics {
  startDate: string;
  endDate: string;
  interval: string;
  currency: string;
  dataPoints: ApiAnalyticsDataPoint[];
}

export interface ApiSubscriptionTierBreakdown {
  planId: number;
  name: string;
  badgeText?: string | null;
  isActive: boolean;
  subscribers: number;
  subscribersPercentage: number;
  revenue: number;
  revenuePercentage: number;
  color?: string;
}

export interface ApiSubscriptionBreakdown {
  startDate: string;
  endDate: string;
  currency: string;
  totalSubscribers: number;
  totalRevenue: number;
  tiers: ApiSubscriptionTierBreakdown[];
}

export interface ApiRecentActivityUser {
  id: number;
  name: string | null;
  email: string | null;
  avatarUrl: string | null;
  planName: string | null;
  isPaid: boolean;
  subscribedAt: string | null;
  joinedAt: string;
}

export async function getDashboardStats(params?: {
  range?: string;
  startDate?: string;
  endDate?: string;
}): Promise<ApiDashboardStats> {
  const query = new URLSearchParams();
  if (params?.range) query.append("range", params.range);
  if (params?.startDate) query.append("start_date", params.startDate);
  if (params?.endDate) query.append("end_date", params.endDate);

  const res = await fetch(`${BASE_URL}/api/v1/admin/dashboard/stats?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  const json = await handleResponse<any>(res);
  return {
    startDate: json.start_date,
    endDate: json.end_date,
    currency: json.currency || "INR",
    totalRevenue: json.total_revenue || { current: 0, previous: 0, growth_percentage: 0 },
    totalViews: json.total_views || { current: 0, previous: 0, growth_percentage: 0 },
    totalUsers: json.total_users || { current: 0, previous: 0, growth_percentage: 0 },
    totalSubscribers: json.total_subscribers || { current: 0, previous: 0, growth_percentage: 0 },
    totalContent: json.total_content || { total: 0, published: 0, drafts: 0, recently_added: 0 },
  };
}

export async function getDashboardAnalytics(params?: {
  range?: string;
  startDate?: string;
  endDate?: string;
  interval?: string;
}): Promise<ApiAnalytics> {
  const query = new URLSearchParams();
  if (params?.range) query.append("range", params.range);
  if (params?.startDate) query.append("start_date", params.startDate);
  if (params?.endDate) query.append("end_date", params.endDate);
  if (params?.interval) query.append("interval", params.interval);

  const res = await fetch(`${BASE_URL}/api/v1/admin/dashboard/analytics?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  const json = await handleResponse<any>(res);
  return {
    startDate: json.start_date,
    endDate: json.end_date,
    interval: json.interval || "month",
    currency: json.currency || "INR",
    dataPoints: (json.data_points || []).map((pt: any) => ({
      date: pt.date,
      label: pt.label,
      users: pt.users ?? 0,
      subscribers: pt.subscribers ?? 0,
      revenue: pt.revenue ?? 0,
      views: pt.views ?? 0,
    })),
  };
}

export async function getDashboardSubscriptionBreakdown(params?: {
  range?: string;
  startDate?: string;
  endDate?: string;
}): Promise<ApiSubscriptionBreakdown> {
  const query = new URLSearchParams();
  if (params?.range) query.append("range", params.range);
  if (params?.startDate) query.append("start_date", params.startDate);
  if (params?.endDate) query.append("end_date", params.endDate);

  const res = await fetch(`${BASE_URL}/api/v1/admin/dashboard/subscription-breakdown?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  const json = await handleResponse<any>(res);
  const palette = ["#8b5cf6", "#3b82f6", "#10b981", "#f59e0b", "#ec4899", "#6366f1"];
  return {
    startDate: json.start_date,
    endDate: json.end_date,
    currency: json.currency || "INR",
    totalSubscribers: json.total_subscribers ?? 0,
    totalRevenue: json.total_revenue ?? 0,
    tiers: (json.tiers || []).map((t: any, idx: number) => ({
      planId: t.plan_id,
      name: t.name,
      badgeText: t.badge_text,
      isActive: t.is_active,
      subscribers: t.subscribers ?? 0,
      subscribersPercentage: t.subscribers_percentage ?? 0,
      revenue: t.revenue ?? 0,
      revenuePercentage: t.revenue_percentage ?? 0,
      color: palette[idx % palette.length],
    })),
  };
}

export async function getDashboardRecentActivity(params?: {
  filter?: "all" | "subscribers" | "users";
  page?: number;
  limit?: number;
}): Promise<{ items: ApiRecentActivityUser[]; total: number; page: number; totalPages: number }> {
  const query = new URLSearchParams();
  if (params?.filter) query.append("filter", params.filter);
  if (params?.page) query.append("page", params.page.toString());
  if (params?.limit) query.append("limit", Math.min(Math.max(params.limit, 1), 20).toString());

  const res = await fetch(`${BASE_URL}/api/v1/admin/dashboard/recent-activity?${query.toString()}`, {
    headers: getAuthHeaders(),
  });
  const json = await handleResponse<any>(res);
  return {
    total: json.total ?? 0,
    page: json.page ?? 1,
    totalPages: json.total_pages ?? 1,
    items: (json.items || []).map((item: any) => ({
      id: item.id,
      name: item.name,
      email: item.email,
      avatarUrl: item.avatar_url,
      planName: item.plan_name,
      isPaid: Boolean(item.is_paid),
      subscribedAt: item.subscribed_at,
      joinedAt: item.joined_at,
    })),
  };
}



