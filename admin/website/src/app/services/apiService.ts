// API Service module for communicating with Content Management backend REST endpoints

function getBaseUrl(): string {
  // When running locally in Vite (dev server at localhost / 127.0.0.1), route through Vite's dev server proxy ("")
  // to completely eliminate browser Cross-Origin (CORS) blocks and ngrok interstitial issues.
  if (
    import.meta.env.DEV ||
    (typeof window !== "undefined" &&
      (window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1" ||
        window.location.hostname === "0.0.0.0"))
  ) {
    return "";
  }

  const envUrl =
    (import.meta as any).env?.VITE_API_BASE_URL ||
    (typeof window !== "undefined" && (window as any).env?.VITE_API_BASE_URL) ||
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
  status: "processing" | "draft" | "scheduled" | "published" | string;
  publishIntent?: "draft" | "publish" | "schedule" | string;
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

export interface ApiAdminUser {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string | null;
  role: string;
  isOwner: boolean;
  isActive: boolean;
  avatarUrl?: string | null;
  createdAt: string;
}

export interface ApiTenant {
  id: number;
  name: string;
  slug: string;
  tagline?: string | null;
  description?: string | null;
  isActive: boolean;
  logoUrl?: string | null;
  deactivationReason?: string | null;
  deactivatedAt?: string | null;
  createdAt: string;
  updatedAt: string;
  adminsCount: number;
  videosCount: number;
  subscribersCount: number;
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
  plan_type?: "with_ads" | "no_ads" | string;
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
  description?: string | null;
  base_price?: number | null;
  discount_percentage?: number | null;
  badge_text?: string | null;
}

// ── Admin Authentication DTOs ──────────────────────────────────────────────

export interface AdminSummary {
  id: number;
  email: string;
  first_name?: string | null;
  last_name?: string | null;
  studio_name?: string | null;
  avatar_url?: string | null;
}

export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  admin: AdminSummary;
}

export interface AdminTokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

// ── Internal Helpers & Auth State ──────────────────────────────────────────

export function setStoredAuth(data: { access_token: string; admin?: AdminSummary }) {
  if (typeof window !== "undefined") {
    localStorage.setItem("access_token", data.access_token);
    if (data.admin) {
      localStorage.setItem("admin_profile", JSON.stringify(data.admin));
    }
  }
}

export function getStoredAdmin(): AdminSummary | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem("admin_profile");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearStoredAuth() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    localStorage.removeItem("admin_profile");
    localStorage.removeItem("current_tenant_id");
  }
}

export function isUserSuperAdmin(): boolean {
  const admin = getStoredAdmin();
  return admin?.role === "super_admin";
}

export function getStoredToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("access_token") || "";
}

function getAuthToken(): string {
  return getStoredToken();
}

function getTenantIdHeader(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("current_tenant_id");
}

function getAuthHeaders(): HeadersInit {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true",
  };
  const tenantId = getTenantIdHeader();
  if (tenantId) {
    headers["X-Tenant-Id"] = tenantId;
  }
  return headers;
}

import { apiMonitorStore } from "./apiMonitorService";

let refreshPromise: Promise<string | null> | null = null;

export async function fetchWithAuth(input: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  if (!headers.has("Content-Type") && !(init?.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const tenantId = getTenantIdHeader();
  if (tenantId && !headers.has("X-Tenant-Id")) {
    headers.set("X-Tenant-Id", tenantId);
  }
  headers.set("ngrok-skip-browser-warning", "true");

  const options: RequestInit = {
    ...init,
    credentials: "include",
    headers,
  };

  let response = await fetch(input, options);

  // If unauthorized (401) and not already calling an auth endpoint, attempt silent refresh
  if (response.status === 401 && !input.includes("/api/v1/admin/auth/")) {
    if (!refreshPromise) {
      refreshPromise = (async () => {
        try {
          const res = await fetch(`${BASE_URL}/api/v1/admin/auth/refresh`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "ngrok-skip-browser-warning": "true",
            },
            credentials: "include",
          });
          if (!res.ok) {
            if (res.status === 401 || res.status === 403) {
              clearStoredAuth();
              if (typeof window !== "undefined" && window.location.pathname !== "/login") {
                window.location.href = "/login";
              }
            }
            throw new Error(`Refresh failed with status ${res.status}`);
          }
          const data = await res.json();
          if (data.access_token) {
            setStoredAuth({ access_token: data.access_token });
            return data.access_token as string;
          }
          return null;
        } catch (err: any) {
          if (err?.message?.includes("401") || err?.message?.includes("403")) {
            clearStoredAuth();
            if (typeof window !== "undefined" && window.location.pathname !== "/login") {
              window.location.href = "/login";
            }
          }
          return null;
        } finally {
          refreshPromise = null;
        }
      })();
    }

    const newToken = await refreshPromise;
    if (newToken) {
      response = await fetch(input, options);
    }
  }

  return response;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    let parsedMessage = errorText || response.statusText;

    // Detect if response is a raw HTML error page (e.g. ngrok offline page, 502/503/504 gateway errors)
    const isHtml =
      errorText.includes("<!DOCTYPE") ||
      errorText.includes("<html") ||
      errorText.includes("<body") ||
      (response.headers.get("content-type") || "").includes("text/html");

    if (isHtml) {
      if (
        errorText.includes("ERR_NGROK_3200") ||
        (errorText.toLowerCase().includes("endpoint") && errorText.toLowerCase().includes("offline"))
      ) {
        parsedMessage = "Something went wrong. Backend server is offline (Ngrok tunnel offline - ERR_NGROK_3200).";
      } else if (response.status === 502) {
        parsedMessage = "Something went wrong. Backend service is currently unreachable (502 Bad Gateway).";
      } else if (response.status === 504) {
        parsedMessage = "Something went wrong. Backend request timed out (504 Gateway Timeout).";
      } else if (response.status === 503) {
        parsedMessage = "Something went wrong. Backend service is temporarily unavailable (503 Service Unavailable).";
      } else {
        parsedMessage = `Something went wrong. Server returned an error page (Status ${response.status}).`;
      }
    } else {
      try {
        const parsed = JSON.parse(errorText);
        if (typeof parsed.error === "string") {
          parsedMessage = parsed.error;
        } else if (typeof parsed.detail === "string") {
          parsedMessage = parsed.detail;
        } else if (Array.isArray(parsed.detail)) {
          parsedMessage = parsed.detail.map((d: any) => d.msg || d.message || JSON.stringify(d)).join(", ");
        } else if (typeof parsed.message === "string") {
          parsedMessage = parsed.message;
        } else if (typeof parsed.msg === "string") {
          parsedMessage = parsed.msg;
        } else if (parsed.detail && typeof parsed.detail === "object" && typeof parsed.detail.message === "string") {
          parsedMessage = parsed.detail.message;
        } else if (parsed.error && typeof parsed.error === "object" && typeof parsed.error.message === "string") {
          parsedMessage = parsed.error.message;
        }
      } catch {
        // If not JSON and error string contains tags or is very long, format cleanly
        if (errorText.includes("<") || errorText.length > 200) {
          parsedMessage = "Something went wrong. Please check your backend connection.";
        }
      }
    }

    apiMonitorStore.addLog({
      url: response.url,
      method: "API",
      status: response.status,
      ok: false,
      data: { error: parsedMessage },
    });
    throw new Error(parsedMessage);
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
    publishIntent: raw.publish_intent || raw.publishIntent || undefined,
    videoType: raw.video_type || raw.videoType || "standard",
    video_type: raw.video_type || raw.videoType || "standard",
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
    isLiked: raw.is_liked ?? raw.isLiked ?? raw.is_hearted_by_creator ?? false,
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
    isLiked: raw.is_hearted_by_creator ?? raw.is_liked ?? raw.isLiked ?? false,
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
  video_type?: "standard" | "shorts" | string;
  videoType?: "standard" | "shorts" | string;
  page?: number;
  limit?: number;
}): Promise<{ data: ApiVideo[]; pagination?: any }> {
  try {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.category) query.append("category", params.category);
    if (params?.video_type || params?.videoType) query.append("video_type", (params.video_type || params.videoType)!);
    if (params?.search) query.append("search", params.search);
    if (params?.sort) query.append("sort", params.sort);
    if (params?.dateFrom) query.append("dateFrom", params.dateFrom);
    if (params?.dateTo) query.append("dateTo", params.dateTo);
    if (params?.page) query.append("page", params.page.toString());
    if (params?.limit) query.append("limit", params.limit.toString());

    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos?${query.toString()}`);
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
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${id}`);
  const json = await handleResponse<any>(res);
  return transformVideo(json.data || json);
}

export async function initiateVideoUpload(data: {
  title: string;
  description?: string;
  category?: string;
  tags?: string[];
  status?: string;
  filename?: string;
  video_type?: "standard" | "shorts" | string;
  videoType?: "standard" | "shorts" | string;
  publish_intent?: "draft" | "publish" | "schedule" | string;
  publishIntent?: "draft" | "publish" | "schedule" | string;
  scheduled_date?: string;
  scheduledDate?: string;
  scheduled_time?: string;
  scheduledTime?: string;
}): Promise<{
  id: number;
  bunnyVideoId?: string;
  bunnyLibraryId?: string;
  uploadUrl?: string;
  signature?: string;
  expirationTime?: number;
  status?: string;
  publishIntent?: string;
  encodeProgress?: number;
}> {
  const intent =
    data.publish_intent ||
    data.publishIntent ||
    (data.status === "published" ? "publish" : data.status === "scheduled" ? "schedule" : "draft");
  const schedDate = data.scheduled_date || data.scheduledDate;
  const schedTime = data.scheduled_time || data.scheduledTime;

  const vType = data.video_type || data.videoType || "standard";
  const payload: any = {
    title: data.title,
    description: data.description,
    video_type: vType,
    tags: data.tags || [],
    publish_intent: intent,
  };
  // Short videos strictly do not use categories
  if (vType !== "shorts" && data.category) {
    payload.category = data.category;
  }
  if (schedDate) payload.scheduled_date = schedDate;
  if (schedTime) payload.scheduled_time = schedTime;

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/initiate`, {
    method: "POST",
    body: JSON.stringify(payload),
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
    publishIntent: json.publish_intent || json.publishIntent,
    encodeProgress: json.encode_progress ?? json.encodeProgress ?? 0,
  };
}

export async function updateVideo(
  id: number,
  data: Partial<ApiVideo> & { video_type?: string }
): Promise<ApiVideo> {
  const payload: any = {};
  if (data.title !== undefined) payload.title = data.title;
  if (data.description !== undefined) payload.description = data.description;
  if (data.category !== undefined) payload.category = data.category;
  if (data.tags !== undefined) payload.tags = data.tags;
  if (data.premium !== undefined) payload.is_premium = data.premium;
  if ((data as any).video_type !== undefined) payload.video_type = (data as any).video_type;

  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${id}`, {
      method: "PATCH",
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
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${id}`, {
    method: "DELETE",
  });
  return handleResponse(res);
}

export async function bulkDeleteVideos(videoIds: number[]): Promise<{ status?: string; success?: boolean }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/bulk-delete`, {
    method: "POST",
    body: JSON.stringify({ video_ids: videoIds }),
  });
  return handleResponse(res);
}

export async function publishVideo(id: number): Promise<ApiVideo> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${id}/publish`, {
    method: "POST",
  });
  const json = await handleResponse<any>(res);
  return transformVideo(json);
}

export async function unpublishVideo(id: number): Promise<ApiVideo> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${id}/unpublish`, {
    method: "POST",
  });
  const json = await handleResponse<any>(res);
  return transformVideo(json);
}

export async function scheduleVideo(
  id: number,
  schedule: { date: string; time: string }
): Promise<ApiVideo> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${id}/schedule`, {
    method: "POST",
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

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${videoId}/thumbnails/upload?slot=${slot}`, {
    method: "POST",
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
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${videoId}/thumbnails/select-main`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function deleteThumbnail(
  videoId: number,
  thumbnailUrl: string
): Promise<{ status?: string; success?: boolean }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/videos/${videoId}/thumbnails`, {
    method: "DELETE",
    body: JSON.stringify({ thumbnail_url: thumbnailUrl }),
  });
  return handleResponse(res);
}

// ── Branding API ────────────────────────────────────────────────────────────

export interface ApiBranding {
  studioName: string;
  creatorName?: string;
  tagline: string;
  description: string;
  bannerUrl: string;
  logoUrl: string;
  updatedAt?: string;
}

function transformBranding(raw: any): ApiBranding {
  if (!raw) return { studioName: "", creatorName: "", tagline: "", description: "", bannerUrl: "", logoUrl: "" };
  const name = raw.studio_name || raw.studioName || raw.creator_name || raw.creatorName || "";
  return {
    studioName: name,
    creatorName: name,
    tagline: raw.tagline || "",
    description: raw.description || "",
    bannerUrl: raw.banner_url || raw.bannerUrl || "",
    logoUrl: raw.logo_url || raw.logoUrl || "",
    updatedAt: raw.updated_at || raw.updatedAt,
  };
}

export async function getCreatorBranding(): Promise<ApiBranding> {
  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/branding`);
    const json = await handleResponse<any>(res);
    return transformBranding(json);
  } catch (err) {
    console.warn("Branding API request failed", err);
    throw err;
  }
}

export async function updateCreatorBranding(data: {
  studio_name?: string;
  studioName?: string;
  creator_name?: string;
  creatorName?: string;
  tagline?: string;
  description?: string;
}): Promise<ApiBranding> {
  const payload: any = {};
  const name = data.studio_name ?? data.studioName ?? data.creator_name ?? data.creatorName;
  if (name !== undefined) {
    payload.studio_name = name;
  }
  if (data.tagline !== undefined) payload.tagline = data.tagline;
  if (data.description !== undefined) payload.description = data.description;

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/branding`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  const json = await handleResponse<any>(res);
  return transformBranding(json);
}

export type BackgroundStyleType = 'pure_black' | 'dark_slate' | 'clean_white' | 'gradient_dark';

export interface MobileAppTheme {
  primaryColor: string;
  activeStateColor: string;
  buttonTextColor: string;
  secondaryColor: string;
  mainBackgroundColor: string;
  cardBackgroundColor: string;
  primaryTextColor: string;
  secondaryTextColor: string;
  mutedTextColor: string;
  backgroundStyle: BackgroundStyleType;
  updatedAt?: string;
}

const THEME_CACHE_KEY = "mobile_app_theme_cache";

const DEFAULT_MOBILE_THEME: MobileAppTheme = {
  primaryColor: "#6366F1", // Royal Indigo
  activeStateColor: "#6366F1",
  buttonTextColor: "#FFFFFF",
  secondaryColor: "#EC4899", // Vivid Rose
  mainBackgroundColor: "#0B0F19",
  cardBackgroundColor: "#161D2B",
  primaryTextColor: "#FFFFFF",
  secondaryTextColor: "#94A3B8",
  mutedTextColor: "#1E293B",
  backgroundStyle: "dark_slate", // Midnight Slate
};

/**
 * Retrieve mobile app theme branding from backend API.
 */
export async function getMobileAppTheme(): Promise<MobileAppTheme> {
  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/branding/theme`);
    const themeObj: MobileAppTheme = {
      primaryColor: data.primaryColor || data.primary_color || DEFAULT_MOBILE_THEME.primaryColor,
      secondaryColor: data.secondaryColor || data.secondary_color || DEFAULT_MOBILE_THEME.secondaryColor,
      activeStateColor: data.activeStateColor || data.active_state_color || DEFAULT_MOBILE_THEME.activeStateColor,
      mainBackgroundColor: data.mainBackgroundColor || data.main_background_color || DEFAULT_MOBILE_THEME.mainBackgroundColor,
      cardBackgroundColor: data.cardBackgroundColor || data.card_background_color || DEFAULT_MOBILE_THEME.cardBackgroundColor,
      primaryTextColor: data.primaryTextColor || data.primary_text_color || DEFAULT_MOBILE_THEME.primaryTextColor,
      secondaryTextColor: data.secondaryTextColor || data.secondary_text_color || DEFAULT_MOBILE_THEME.secondaryTextColor,
      mutedTextColor: data.mutedTextColor || data.muted_text_color || DEFAULT_MOBILE_THEME.mutedTextColor,
      buttonTextColor: data.buttonTextColor || data.button_text_color || DEFAULT_MOBILE_THEME.buttonTextColor,
      backgroundStyle: data.backgroundStyle || data.background_style || DEFAULT_MOBILE_THEME.backgroundStyle,
      updatedAt: data.updatedAt || data.updated_at || new Date().toISOString(),
    };
    try {
      localStorage.setItem(THEME_CACHE_KEY, JSON.stringify(themeObj));
    } catch {}
    return themeObj;
  } catch (err) {
    console.warn("Backend theme endpoint error:", err);
    try {
      const raw = localStorage.getItem(THEME_CACHE_KEY);
      if (raw) return JSON.parse(raw);
    } catch {}
    return { ...DEFAULT_MOBILE_THEME };
  }
}

export async function updateMobileAppTheme(theme: Partial<MobileAppTheme>): Promise<MobileAppTheme> {
  const payload = {
    primaryColor: theme.primaryColor,
    secondaryColor: theme.secondaryColor,
    activeStateColor: theme.activeStateColor || theme.primaryColor,
    mainBackgroundColor: theme.mainBackgroundColor,
    cardBackgroundColor: theme.cardBackgroundColor,
    primaryTextColor: theme.primaryTextColor,
    secondaryTextColor: theme.secondaryTextColor,
    mutedTextColor: theme.mutedTextColor,
    buttonTextColor: theme.buttonTextColor,
  };
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/branding/theme`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  const data = await handleResponse<any>(res);
  const updated: MobileAppTheme = {
    primaryColor: data.primaryColor || data.primary_color || theme.primaryColor || DEFAULT_MOBILE_THEME.primaryColor,
    secondaryColor: data.secondaryColor || data.secondary_color || theme.secondaryColor || DEFAULT_MOBILE_THEME.secondaryColor,
    activeStateColor: data.activeStateColor || data.active_state_color || theme.activeStateColor || DEFAULT_MOBILE_THEME.activeStateColor,
    mainBackgroundColor: data.mainBackgroundColor || data.main_background_color || theme.mainBackgroundColor || DEFAULT_MOBILE_THEME.mainBackgroundColor,
    cardBackgroundColor: data.cardBackgroundColor || data.card_background_color || theme.cardBackgroundColor || DEFAULT_MOBILE_THEME.cardBackgroundColor,
    primaryTextColor: data.primaryTextColor || data.primary_text_color || theme.primaryTextColor || DEFAULT_MOBILE_THEME.primaryTextColor,
    secondaryTextColor: data.secondaryTextColor || data.secondary_text_color || theme.secondaryTextColor || DEFAULT_MOBILE_THEME.secondaryTextColor,
    mutedTextColor: data.mutedTextColor || data.muted_text_color || theme.mutedTextColor || DEFAULT_MOBILE_THEME.mutedTextColor,
    buttonTextColor: data.buttonTextColor || data.button_text_color || theme.buttonTextColor || DEFAULT_MOBILE_THEME.buttonTextColor,
    backgroundStyle: data.backgroundStyle || data.background_style || DEFAULT_MOBILE_THEME.backgroundStyle,
    updatedAt: data.updatedAt || data.updated_at || new Date().toISOString(),
  };
  try {
    localStorage.setItem(THEME_CACHE_KEY, JSON.stringify(updated));
  } catch {}
  window.dispatchEvent(new CustomEvent("mobile_theme_updated", { detail: updated }));
  return updated;
}

export async function uploadCreatorLogo(file: File): Promise<{ logoUrl: string }> {
  const formData = new FormData();
  formData.append("logo", file);

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/branding/logo`, {
    method: "POST",
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

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/branding/banner`, {
    method: "POST",
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
    let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/featured-videos`);
    if (res.status === 404) {
      res = await fetchWithAuth(`${BASE_URL}/featured-videos`);
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
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/featured-videos`, {
    method: "PUT",
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/featured-videos`, {
      method: "PUT",
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
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/featured-videos`, {
    method: "POST",
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/featured-videos`, {
      method: "POST",
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
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/featured-videos/reorder`, {
    method: "PUT",
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/featured-videos/reorder`, {
      method: "PUT",
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }
  await handleResponse<any>(res);
  return true;
}

export async function deleteFeaturedVideo(videoId: number): Promise<boolean> {
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/featured-videos/${videoId}`, {
    method: "DELETE",
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/featured-videos/${videoId}`, {
      method: "DELETE",
    });
  }
  await handleResponse<any>(res);
  return true;
}

export async function bulkDeleteFeaturedVideos(videoIds: number[]): Promise<boolean> {
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/featured-videos`, {
    method: "DELETE",
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/featured-videos`, {
      method: "DELETE",
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

    let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/featured-videos/available?${query.toString()}`);
    if (res.status === 404) {
      res = await fetchWithAuth(`${BASE_URL}/featured-videos/available?${query.toString()}`);
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

    let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists?${query.toString()}`);
    if (res.status === 404) {
      res = await fetchWithAuth(`${BASE_URL}/playlists?${query.toString()}`);
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

  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists`, {
    method: "POST",
    body: JSON.stringify({
      name: nameVal,
      description: descVal,
      video_ids: videoIds,
    }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists`, {
      method: "POST",
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

  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  }
  const json = await handleResponse<any>(res);
  return transformPlaylist(json);
}

export async function deletePlaylist(id: number): Promise<{ status?: string; success?: boolean }> {
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists/${id}`, {
    method: "DELETE",
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists/${id}`, {
      method: "DELETE",
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

  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/thumbnail/upload`, {
    method: "POST",
    body: formData,
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists/${playlistId}/thumbnail/upload`, {
      method: "POST",
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

  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos?${query.toString()}`);
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists/${playlistId}/videos?${query.toString()}`);
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
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos`, {
    method: "POST",
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists/${playlistId}/videos`, {
      method: "POST",
      body: JSON.stringify({ video_ids: videoIds }),
    });
  }
  return handleResponse(res);
}

export async function removeVideoFromPlaylist(
  playlistId: number,
  videoId: number
): Promise<{ status?: string; success?: boolean }> {
  let res = await fetchWithAuth(
    `${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos/${videoId}`,
    {
      method: "DELETE",
    }
  );
  if (res.status === 404) {
    res = await fetchWithAuth(
      `${BASE_URL}/playlists/${playlistId}/videos/${videoId}`,
      {
        method: "DELETE",
      }
    );
  }
  return handleResponse(res);
}

export async function bulkRemoveVideosFromPlaylist(
  playlistId: number,
  videoIds: number[]
): Promise<{ status?: string; success?: boolean }> {
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos`, {
    method: "DELETE",
    body: JSON.stringify({ video_ids: videoIds }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists/${playlistId}/videos`, {
      method: "DELETE",
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

  let res = await fetchWithAuth(
    `${BASE_URL}/api/v1/admin/playlists/${playlistId}/available_videos?${query.toString()}`
  );
  if (res.status === 404) {
    res = await fetchWithAuth(
      `${BASE_URL}/playlists/${playlistId}/available_videos?${query.toString()}`
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
  let res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/playlists/${playlistId}/videos/reorder`, {
    method: "PUT",
    body: JSON.stringify({ video_orders: videoOrders }),
  });
  if (res.status === 404) {
    res = await fetchWithAuth(`${BASE_URL}/playlists/${playlistId}/videos/reorder`, {
      method: "PUT",
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

    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/comments?${query.toString()}`);
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
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/comments/videos/${videoId}/comments`, {
    method: "POST",
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

  const res = await fetchWithAuth(
    `${BASE_URL}/api/v1/admin/comments/${commentId}/replies?${query.toString()}`
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
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/comments/${commentId}/reply`, {
    method: "POST",
    body: JSON.stringify({ text }),
  });
  const json = await handleResponse<any>(res);
  return transformReply(json);
}

export async function toggleCommentLike(
  commentId: number
): Promise<{ status: string; isLiked: boolean; likes: number }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/comments/${commentId}/like`, {
    method: "POST",
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
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/comments/${commentId}`, {
    method: "DELETE",
  });
  return handleResponse(res);
}

// ── Settings / Profile API ─────────────────────────────────────────────────

export async function getCreatorProfile(): Promise<ApiProfile> {
  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/profile`);
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
    avatar_url: string;
    bio: string;
    website: string;
    phone: string;
    location: string;
    social_links: ApiSocialLinks;
  }>
): Promise<{ status?: string; success?: boolean }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/profile`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function uploadAvatarPhoto(
  file: File
): Promise<{ avatarUrl: string }> {
  const formData = new FormData();
  formData.append("photo", file);

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/profile/photo`, {
    method: "POST",
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
        revenue: item.isPaid ? "Paid" : "₹0",
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
  thumbnailUrl?: string;
  icon?: string;
  color: string;
  contentCount: number;
  order: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateCategoryPayload {
  name: string;
  description?: string;
  color?: string;
}

export interface UpdateCategoryPayload {
  name?: string;
  description?: string;
  color?: string;
}

function transformCategory(raw: any): ApiCategory {
  return {
    id: raw.id,
    name: raw.name || "Untitled Category",
    slug: raw.slug || "",
    description: raw.description || "",
    thumbnailUrl: raw.thumbnailUrl || raw.thumbnail_url || undefined,
    icon: raw.icon || undefined,
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

    const res = await fetchWithAuth(url);
    const json = await handleResponse<any>(res);
    const list = json.data || json.items || (Array.isArray(json) ? json : []);
    return list.map(transformCategory);
  } catch (err) {
    console.warn("Categories API request failed", err);
    throw err;
  }
}

export async function createCategory(data: CreateCategoryPayload): Promise<ApiCategory> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/categories`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  const json = await handleResponse<any>(res);
  return transformCategory(json);
}

export async function updateCategory(id: number, data: UpdateCategoryPayload): Promise<ApiCategory> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/categories/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  const json = await handleResponse<any>(res);
  return transformCategory(json);
}

export async function uploadCategoryThumbnail(
  categoryId: number,
  file: File
): Promise<{ thumbnailUrl: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/categories/${categoryId}/thumbnail/upload`, {
    method: "POST",
    body: formData,
  });
  const json = await handleResponse<any>(res);
  return {
    thumbnailUrl: json.thumbnail_url || json.thumbnailUrl || "",
  };
}

export async function deleteCategory(id: number): Promise<{ message: string }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/categories/${id}`, {
    method: "DELETE",
  });
  return handleResponse(res);
}

export async function reorderCategories(ids: number[]): Promise<{ message: string }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/categories/reorder`, {
    method: "PUT",
    body: JSON.stringify({ ids }),
  });
  return handleResponse(res);
}

// ── Admin Authentication API Endpoints ─────────────────────────────────────

export async function adminLogin(payload: { email: string; password: string }): Promise<AdminLoginResponse> {
  if (typeof window !== "undefined") {
    localStorage.removeItem("user_logged_out");
  }
  const res = await fetch(`${BASE_URL}/api/v1/admin/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });
  const data = await handleResponse<AdminLoginResponse>(res);
  clearStoredAuth();
  if (typeof window !== "undefined") {
    localStorage.removeItem("user_logged_out");
  }
  setStoredAuth({ access_token: data.access_token, admin: data.admin });
  return data;
}

export async function adminRefresh(): Promise<AdminTokenResponse> {
  if (typeof window !== "undefined" && localStorage.getItem("user_logged_out") === "true") {
    throw new Error("Session terminated: user explicitly logged out.");
  }
  const res = await fetch(`${BASE_URL}/api/v1/admin/auth/refresh`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "ngrok-skip-browser-warning": "true",
    },
    credentials: "include",
  });
  const data = await handleResponse<AdminTokenResponse>(res);
  if (data?.access_token) {
    setStoredAuth({ access_token: data.access_token });
  }
  return data;
}

export async function adminGetMe(): Promise<AdminSummary> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/auth/me`);
  const data = await handleResponse<AdminSummary>(res);
  if (data) {
    localStorage.setItem("admin_profile", JSON.stringify(data));
  }
  return data;
}

export async function adminLogout(): Promise<void> {
  if (typeof window !== "undefined") {
    localStorage.setItem("user_logged_out", "true");
  }
  clearStoredAuth();

  try {
    await fetch(`${BASE_URL}/api/v1/admin/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
      },
      credentials: "include",
    });
  } catch (err) {
    console.warn("Logout request failed", err);
  }
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
}

export async function changeAdminPassword(payload: ChangePasswordPayload): Promise<{ status: string }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/auth/change-password`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return await handleResponse<{ status: string }>(res);
}

// ── Subscription Plans API Endpoints ────────────────────────────────────────

export async function getSubscriptionPlans(): Promise<ApiSubscriptionPlan[]> {
  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/plans`);
    const json = await handleResponse<any>(res);
    return Array.isArray(json) ? json : json.data || json.items || [];
  } catch (err) {
    console.warn("[API Service] Subscription Plans API request failed", err);
    throw err;
  }
}

export async function updateSubscriptionPlan(
  planId: number,
  data: UpdateSubscriptionPlanPayload
): Promise<ApiSubscriptionPlan> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/plans/${planId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
  return handleResponse<ApiSubscriptionPlan>(res);
}

// Deprecated legacy plan endpoints retained as safe stubs for component compatibility
export async function createSubscriptionPlan(data: CreateSubscriptionPlanPayload): Promise<ApiSubscriptionPlan> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/plans`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return handleResponse<ApiSubscriptionPlan>(res);
}

export async function deleteSubscriptionPlan(planId: number): Promise<{ message: string }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/plans/${planId}`, {
    method: "DELETE",
  });
  return handleResponse(res);
}

export async function toggleSubscriptionPlanActive(
  planId: number
): Promise<{ id: number; name: string; is_active: boolean; updated_at: string }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/plans/${planId}/toggle-active`, {
    method: "PATCH",
  });
  return handleResponse(res);
}

export async function reorderSubscriptionPlans(ids: number[]): Promise<{ message: string }> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/plans/reorder`, {
    method: "PUT",
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
  scheduled: number;
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

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/dashboard/stats?${query.toString()}`);
  const json = await handleResponse<any>(res);
  return {
    startDate: json.start_date,
    endDate: json.end_date,
    currency: json.currency || "INR",
    totalRevenue: json.total_revenue || { current: 0, previous: 0, growth_percentage: 0 },
    totalViews: json.total_views || { current: 0, previous: 0, growth_percentage: 0 },
    totalUsers: json.total_users || { current: 0, previous: 0, growth_percentage: 0 },
    totalSubscribers: json.total_subscribers || { current: 0, previous: 0, growth_percentage: 0 },
    totalContent: {
      total: json.total_content?.total ?? 0,
      published: json.total_content?.published ?? 0,
      drafts: json.total_content?.drafts ?? 0,
      scheduled: json.total_content?.scheduled ?? 0,
      recently_added: json.total_content?.recently_added ?? 0,
    },
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

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/dashboard/analytics?${query.toString()}`);
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

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/dashboard/subscription-breakdown?${query.toString()}`);
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
      badgeText: t.badge_text ?? null,
      isActive: t.is_active ?? true,
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

  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/dashboard/recent-activity?${query.toString()}`);
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

// ── Monetization & Settlements Interfaces ───────────────────────────────────

export interface CurrentPeriodSummary {
  period: string;
  estimated_earnings: number | null;
  impressions: number;
  ecpm: number | null;
  expected_payout_date: string;
}

export interface PendingPayoutSummary {
  period: string;
  amount: number;
  status: "reconciled" | "pending_bank_details" | string;
  payout_date: string;
}

export interface LastPayoutSummary {
  period: string;
  amount: number;
  payout_date: string;
  utr: string | null;
}

export interface ApiMonetizationSummary {
  currency: string;
  payout_profile_configured: boolean;
  current_period: CurrentPeriodSummary;
  pending_payout: PendingPayoutSummary | null;
  last_payout: LastPayoutSummary | null;
  lifetime_earnings: number;
}

export interface MonetizationAnalyticsPoint {
  date: string;
  impressions: number;
  ecpm: number | null;
  estimated_earnings: number | null;
}

export interface ApiMonetizationAnalytics {
  start_date: string;
  end_date: string;
  interval: string;
  currency: string;
  data_points: MonetizationAnalyticsPoint[];
}

export interface ApiSettlementItem {
  statement_id: string;
  month: string;
  impressions_count: number;
  ecpm: number;
  amount: number;
  currency: string;
  status: "accruing" | "pending_bank_details" | "reconciled" | "paid" | string;
  settled_at: string | null;
  transaction_reference: string | null;
  invoice_url: string | null;
}

export interface ApiSettlementsResponse {
  items: ApiSettlementItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface ApiPayoutProfile {
  account_holder_name: string | null;
  bank_name: string | null;
  account_number_masked: string | null;
  ifsc_code: string | null;
  updated_at: string | null;
}

export interface UpdatePayoutProfilePayload {
  account_holder_name: string;
  account_number: string;
  ifsc_code: string;
}

// ── Monetization & Settlements Endpoints ────────────────────────────────────

export async function getMonetizationSummary(): Promise<ApiMonetizationSummary> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/monetization/summary`);
  return handleResponse<ApiMonetizationSummary>(res);
}

export async function getMonetizationAnalytics(params?: {
  range?: string;
  start_date?: string;
  end_date?: string;
  interval?: string;
}): Promise<ApiMonetizationAnalytics> {
  const query = new URLSearchParams();
  if (params?.range) query.append("range", params.range);
  if (params?.start_date) query.append("start_date", params.start_date);
  if (params?.end_date) query.append("end_date", params.end_date);
  if (params?.interval) query.append("interval", params.interval);

  const qs = query.toString();
  const url = `${BASE_URL}/api/v1/admin/monetization/analytics${qs ? `?${qs}` : ""}`;
  const res = await fetchWithAuth(url);
  return handleResponse<ApiMonetizationAnalytics>(res);
}

export async function getMonetizationSettlements(params?: {
  page?: number;
  limit?: number;
}): Promise<ApiSettlementsResponse> {
  const query = new URLSearchParams();
  if (params?.page) query.append("page", params.page.toString());
  if (params?.limit) query.append("limit", params.limit.toString());

  const qs = query.toString();
  const url = `${BASE_URL}/api/v1/admin/monetization/settlements${qs ? `?${qs}` : ""}`;
  const res = await fetchWithAuth(url);
  return handleResponse<ApiSettlementsResponse>(res);
}

export async function getPayoutSettings(): Promise<ApiPayoutProfile> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/monetization/settings`);
  return handleResponse<ApiPayoutProfile>(res);
}

export async function updatePayoutSettings(
  payload: UpdatePayoutProfilePayload
): Promise<ApiPayoutProfile> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/monetization/settings`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
  return handleResponse<ApiPayoutProfile>(res);
}

// ── Tenant User Management Endpoints ────────────────────────────────────────

export interface TenantUser {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  isActive?: boolean;
  is_owner?: boolean;
  isOwner?: boolean;
  role?: string;
  avatar_url?: string | null;
  avatarUrl?: string | null;
  created_at?: string;
  createdAt?: string;
}

export async function getTenantUsers(): Promise<TenantUser[]> {
  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/users`);
    const json = await handleResponse<any>(res);
    const rawList = Array.isArray(json) ? json : json.data || json.items || json.users || [];
    return rawList.map((u: any) => ({
      id: u.id ?? u.user_id,
      email: u.email,
      first_name: u.first_name || u.firstName || "",
      last_name: u.last_name || u.lastName || "",
      is_active: u.is_active ?? u.isActive ?? true,
      isActive: u.is_active ?? u.isActive ?? true,
      is_owner: !!(u.is_owner ?? u.isOwner ?? false),
      isOwner: !!(u.is_owner ?? u.isOwner ?? false),
      role: u.role || (u.is_owner || u.isOwner ? "Owner" : "Admin"),
      avatar_url: u.avatar_url || u.avatarUrl || null,
      avatarUrl: u.avatar_url || u.avatarUrl || null,
      created_at: u.created_at || u.createdAt || "",
    }));
  } catch (err) {
    console.warn("[API Service] Failed to fetch tenant users:", err);
    throw err;
  }
}

export async function createTenantUser(payload: {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}): Promise<TenantUser> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/users`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const json = await handleResponse<any>(res);
  const u = json.data || json.user || json;
  return {
    id: u.id ?? u.user_id,
    email: u.email,
    first_name: u.first_name || u.firstName || "",
    last_name: u.last_name || u.lastName || "",
    is_active: u.is_active ?? u.isActive ?? true,
    isActive: u.is_active ?? u.isActive ?? true,
    created_at: u.created_at || u.createdAt || new Date().toISOString(),
  };
}

export async function deleteTenantUser(userId: number): Promise<void> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/users/${userId}`, {
    method: "DELETE",
  });
  if (!res.ok && res.status !== 204) {
    await handleResponse<any>(res);
  }
}

export async function toggleTenantUserActive(
  userId: number,
  currentStatus: boolean
): Promise<{ success: boolean; is_active: boolean; isActive: boolean }> {
  const newStatus = !currentStatus;
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/users/${userId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: newStatus }),
  });
  const json = await handleResponse<any>(res);
  const updatedStatus = json.is_active ?? json.isActive ?? newStatus;
  return {
    success: json.success ?? true,
    is_active: updatedStatus,
    isActive: updatedStatus,
  };
}

// ── Short Videos (Shorts) Management Endpoints ──────────────────────────────

export interface ApiShortVideo {
  id: number;
  title: string;
  description?: string;
  category?: string;
  videoUrl: string;
  thumbnailUrl: string;
  duration: string;
  durationSeconds: number;
  aspectRatio: string;
  width: number;
  height: number;
  views: number;
  likes: number;
  status: "Published" | "Draft" | "Scheduled";
  tags: string[];
  createdAt: string;
  date?: string;
}

export async function getShortVideos(): Promise<ApiShortVideo[]> {
  try {
    const res = await getVideos({ video_type: "shorts", limit: 100 });
    if (res && res.data) {
      const mapped = await Promise.all(
        res.data.map(async (v) => {
          let item = v;
          const statusLower = (v.status || "").toLowerCase();
          if (["pending", "processing", "encoding", "uploading"].includes(statusLower)) {
            try {
              const detailed = await getVideoDetails(v.id);
              if (detailed) {
                item = detailed;
              }
            } catch {
              // Ignore individual sync error, fallback to list item
            }
          }
          const rawDate = item.date || item.createdAt || (item as any).created_at || (item as any).published_at;
          const formattedDate = rawDate
            ? (typeof rawDate === "string" && rawDate.includes("T") ? rawDate.split("T")[0] : String(rawDate).slice(0, 10))
            : new Date().toISOString().split("T")[0];

          return {
            id: item.id,
            title: item.title,
            description: item.description,
            category: "Shorts",
            videoUrl: item.playbackUrl || item.videoUrl || "",
            thumbnailUrl: item.mainThumbnailUrl || item.thumbnailUrl || "",
            duration: item.duration || "0:30",
            durationSeconds: 30,
            aspectRatio: "9:16",
            width: 1080,
            height: 1920,
            views: item.views || 0,
            likes: item.likes || 0,
            status: (item.status ? item.status.charAt(0).toUpperCase() + item.status.slice(1).toLowerCase() : "Draft") as any,
            tags: item.tags || [],
            createdAt: item.createdAt || new Date().toISOString(),
            date: formattedDate,
          };
        })
      );
      return mapped;
    }
  } catch (err) {
    console.warn("Failed to fetch shorts from backend API:", err);
  }
  return [];
}

export async function deleteShortVideo(id: number): Promise<{ success: boolean; message?: string }> {
  return await deleteVideo(id);
}

export async function toggleShortVideoLike(id: number): Promise<{ likes: number; liked: boolean }> {
  return { likes: 0, liked: true };
}




// ── Admin Users API ──────────────────────────────────────────────────────────

export async function getAdminUsers(): Promise<ApiAdminUser[]> {
  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/users`);
    const json = await handleResponse<any>(res);
    return (json || []).map((u: any) => ({
      id: u.id,
      email: u.email,
      firstName: u.first_name || u.firstName,
      lastName: u.last_name || u.lastName,
      phone: u.phone,
      role: u.role,
      isOwner: u.is_owner || u.isOwner,
      isActive: u.is_active || u.isActive,
      avatarUrl: u.avatar_url || u.avatarUrl,
      createdAt: u.created_at || u.createdAt,
    }));
  } catch (err) {
    console.warn("getAdminUsers failed", err);
    throw err;
  }
}

export async function addAdminUser(data: {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
}): Promise<ApiAdminUser> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/users`, {
    method: "POST",
    body: JSON.stringify({
      email: data.email,
      password: data.password,
      first_name: data.firstName,
      last_name: data.lastName,
    }),
  });
  const u = await handleResponse<any>(res);
  return {
    id: u.id,
    email: u.email,
    firstName: u.first_name || u.firstName,
    lastName: u.last_name || u.lastName,
    phone: u.phone,
    role: u.role,
    isOwner: u.is_owner || u.isOwner,
    isActive: u.is_active || u.isActive,
    avatarUrl: u.avatar_url || u.avatarUrl,
    createdAt: u.created_at || u.createdAt,
  };
}

export async function updateAdminUserStatus(id: number, isActive: boolean): Promise<ApiAdminUser> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/users/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
  const u = await handleResponse<any>(res);
  return {
    id: u.id,
    email: u.email,
    firstName: u.first_name || u.firstName,
    lastName: u.last_name || u.lastName,
    phone: u.phone,
    role: u.role,
    isOwner: u.is_owner || u.isOwner,
    isActive: u.is_active || u.isActive,
    avatarUrl: u.avatar_url || u.avatarUrl,
    createdAt: u.created_at || u.createdAt,
  };
}

// ── Super Admin Tenants API ──────────────────────────────────────────────────

export async function getTenants(mode: "compact" | "detailed" = "detailed"): Promise<ApiTenant[]> {
  try {
    const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/tenants?mode=${mode}`);
    const json = await handleResponse<any>(res);
    const items = json.items || json.data || json || [];
    return items.map((t: any) => ({
      id: t.id,
      name: t.name,
      slug: t.slug,
      tagline: t.tagline,
      description: t.description,
      isActive: t.is_active || t.isActive,
      logoUrl: t.logo_url || t.logoUrl,
      deactivationReason: t.deactivation_reason || t.deactivationReason,
      deactivatedAt: t.deactivated_at || t.deactivatedAt,
      createdAt: t.created_at || t.createdAt,
      updatedAt: t.updated_at || t.updatedAt,
      adminsCount: t.admins_count || t.adminsCount || 0,
      videosCount: t.videos_count || t.videosCount || 0,
      subscribersCount: t.subscribers_count || t.subscribersCount || 0,
    }));
  } catch (err) {
    console.warn("getTenants failed", err);
    throw err;
  }
}

export async function createTenant(data: {
  name: string;
  adminEmail: string;
  adminPassword: string;
  adminFirstName: string;
  adminLastName: string;
  description?: string;
  tagline?: string;
}): Promise<any> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/tenants`, {
    method: "POST",
    body: JSON.stringify({
      name: data.name,
      admin_email: data.adminEmail,
      admin_password: data.adminPassword,
      admin_first_name: data.adminFirstName,
      admin_last_name: data.adminLastName,
      description: data.description,
      tagline: data.tagline,
    }),
  });
  return await handleResponse<any>(res);
}

export async function updateTenantStatus(id: number, isActive: boolean, reason?: string): Promise<any> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/tenants/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive, deactivation_reason: reason }),
  });
  return await handleResponse<any>(res);
}

// ── Super Admin Ad Reconciliation & Monthly Settlements ─────────────────────

export interface TenantStatementDraft {
  tenant_id: number;
  tenant_name: string;
  impressions_count: number;
  net_ecpm: number;
  net_amount: number;
  gross_revenue: number;
  platform_fee: number;
}

export interface TenantStatementPublished {
  tenant_id: number;
  tenant_name: string;
  statement_id: string;
  impressions_count: number;
  net_ecpm: number;
  net_amount: number;
  gross_revenue: number;
  platform_fee: number;
  status: string;
  scheduled_payout_date?: string;
}

export interface PlatformReconciliationDraftResponse {
  id: number;
  month: string;
  total_google_revenue: number;
  total_impressions: number;
  gross_ecpm: number;
  platform_commission_pct: number;
  platform_profit: number;
  creator_pool_amount: number;
  creator_net_ecpm: number;
  creators_count: number;
  currency: string;
  status: string;
  notes?: string;
  statements: TenantStatementDraft[];
}

export interface PublishReconciliationResponse {
  id: number;
  month: string;
  total_google_revenue: number;
  status: string;
  currency: string;
  creator_pool_amount: number;
  platform_profit: number;
  reconciled_at: string;
  statements: TenantStatementPublished[];
}

export interface SettledStatementResponse {
  statement_id: string;
  tenant_id: number;
  month: string;
  amount: number;
  currency: string;
  status: string;
  transaction_reference: string;
  settled_at: string;
}

export interface ReconciliationListItem {
  id: number;
  month: string;
  total_google_revenue: number;
  platform_profit: number;
  creator_pool_amount: number;
  currency: string;
  status: string;
  reconciled_at?: string;
}

export async function generateReconciliationDraft(data: {
  month: string;
  gross_revenue: number;
  notes?: string;
}): Promise<PlatformReconciliationDraftResponse> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/monetization/reconciliations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return await handleResponse<PlatformReconciliationDraftResponse>(res);
}

export async function publishReconciliation(month: string): Promise<PublishReconciliationResponse> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/monetization/reconciliations/${month}/publish`, {
    method: "POST",
  });
  return await handleResponse<PublishReconciliationResponse>(res);
}

export async function markStatementPaid(statementId: string, data: {
  transaction_reference: string;
  invoice_url?: string;
}): Promise<SettledStatementResponse> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/monetization/settlements/${statementId}/mark-paid`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  return await handleResponse<SettledStatementResponse>(res);
}

export async function getReconciliationLedger(page = 1, limit = 12): Promise<{
  items: ReconciliationListItem[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}> {
  const res = await fetchWithAuth(`${BASE_URL}/api/v1/admin/monetization/reconciliations?page=${page}&limit=${limit}`);
  return await handleResponse<any>(res);
}
