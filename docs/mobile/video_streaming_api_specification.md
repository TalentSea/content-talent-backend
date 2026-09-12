# Mobile Video Streaming API Specification (Adaptive HLS & Offline MP4 Downloads)

This specification defines the production-grade **Mobile Video Streaming & Catalog Endpoints** for mobile applications (iOS & Android / Flutter & React Native).

---

## 🏛️ Architecture Overview

The video streaming subsystem integrates FastAPI with **Bunny Stream CDN Infrastructure** to provide secure, high-performance adaptive bitrate streaming (**HLS / m3u8**), presigned **offline MP4 video downloads**, and **real-time Watch History & Continue Watching playback synchronization**.

### 1. HLS & MP4 Download Architecture
```
┌─────────────────┐       GET /api/v1/mobile/videos/{video_id}      ┌─────────────────────────┐
│ Mobile App      │ ──────────────────────────────────────────────► │ FastAPI Backend         │
│ (iOS / Android) │ ◄────────────────────────────────────────────── │ (Peewee ORM & Token Sign)│
└────────┬────────┘    Returns Presigned HLS & MP4 Download URLs    └─────────────────────────┘
         │
         │ 1. HLS Stream (playlist.m3u8?token=...&expires=...)
         │ 2. MP4 Download (play_720p.mp4?token=...&expires=...)
         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Bunny Stream Global CDN                                                                     │
│ • Adaptive Bitrate HLS (1080p, 720p, 480p, 360p) with Token Authentication Security           │
│ • Presigned MP4 Video File Downloads                                                        │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Watch History & Continue Watching Flowchart
```
┌─────────────────┐      Every 10 seconds / On Pause      ┌─────────────────────────┐
│ Mobile Player   │ ────────────────────────────────────► │ FastAPI Backend         │
│ (Flutter/iOS)   │ POST /videos/{id}/progress            │ Upserts watch_history   │
└────────┬────────┘ { "progress_seconds": 425 }           └────────────┬────────────┘
         │                                                             │
         │ 1. Tap thumbnail in "Continue Watching"                     │ 2. Queries unfinished videos
         ▼                                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ Video Player seeks to 425s automatically: player.seekTo(Duration(seconds: 425))         │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security & Authorization Rules Matrix

The mobile video subsystem strictly enforces Role-Based Access Control (RBAC) across all endpoints:

1. **`GET /api/v1/mobile/videos` (Catalog Feed & Search)**:
   - **Guarded by**: `Depends(get_current_subscriber)`
   - **Header**: `Authorization: Bearer <access_token>` (**Required**)
   - **Multi-Tenant Isolation**: Decodes `current_subscriber["creator_id"]` from JWT claims (< 1ms) and filters catalog queries (`Video.select().where(Video.user == creator_id)`).
   - **Allowed Roles**: Both `guest` AND `subscriber`
   - **Behavior**: Rejects requests missing a Bearer token with `HTTP 401 Unauthorized`. Accepts Guest tokens for catalog browsing, and Subscriber tokens for browsing + personalized progress.

2. **`GET /api/v1/mobile/videos/{video_id}` (Video Player & HLS Stream)**:
   - **Guarded by**: `Depends(get_current_subscriber)`
   - **Header**: `Authorization: Bearer <access_token>` (**Required**)
   - **Allowed Roles**: Strictly `subscriber` (and creator/admin)
   - **Behavior**: Blocks Guest accounts with `HTTP 403 Forbidden` (`"Subscriber access required"`). Forces Guests to sign in with Google or Facebook to stream videos!

3. **Protected Subscriber Actions**:
   - **Guarded by**: `Depends(get_current_subscriber)`
   - **Endpoints**:
     - `POST /api/v1/mobile/videos/{id}/progress` *(Watch Progress Heartbeat)*
     - `GET /api/v1/mobile/videos/continue-watching` *(Continue Watching Feed)*
     - `GET /api/v1/mobile/videos/history` *(Full Watch History Feed)*
     - `DELETE /api/v1/mobile/videos/history` *(Clear All Watch History)*
     - `DELETE /api/v1/mobile/videos/history/{id}` *(Remove Single Video)*
     - `GET /api/v1/mobile/videos/liked` *(My Liked Videos)*
     - `GET /api/v1/mobile/videos/saved` *(My Saved Videos / Watchlist)*
     - `POST /api/v1/mobile/videos/{id}/like` *(Toggle Video Like)*
     - `POST /api/v1/mobile/videos/{id}/save` *(Toggle Video Save)*
   - **Behavior**: All strictly enforce `Depends(get_current_subscriber)`. Rejects Guests with `HTTP 403 Forbidden`.

---

## 🔒 Strict Visibility & Video Readiness Filtering

To ensure a 100% bug-free mobile subscriber playback experience, all public mobile video APIs enforce two mandatory database filters:

```sql
WHERE status = 'published' 
  AND transcoding_status = 'READY'
```

### 1. Mandatory Filtering Rules
* **`status = 'published'`**: Strictly hides unreleased draft videos (`status = 'draft'`) and future scheduled releases (`status = 'scheduled'`) from mobile subscribers.
* **`transcoding_status = 'READY'`**: Ensures Bunny Stream CDN has completed multi-resolution encoding (1080p, 720p, 480p, 360p) and generated valid HLS playlists (`playlist.m3u8`). Videos that are `ENCODING` or `FAILED` are automatically hidden to prevent mobile player errors.

### 2. Automated Scheduled Video Publishing
The backend operates an automated background worker (`scheduled_video_auto_publisher`) that scans every 60 seconds. When a scheduled video's publication time (`scheduled_publish_at`) is reached, it automatically updates `status = 'published'`. The video immediately appears at the top of the mobile video feed!

---

## 🔌 API Endpoints Specification

### 1. `GET /api/v1/mobile/videos` — Public Video Feed & Search Catalog

Retrieves a paginated, filterable list of published, ready-to-stream video assets for mobile home feed, category tabs, and search results.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required: Accepts Guest token for browsing, Subscriber token for browsing + personalized progress)
```

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `category` | `string` | No | `null` | Filter videos by category slug (e.g. `tech`, `tutorials`, `vlogs`) |
| `search` | `string` | No | `null` | Search video title by substring |
| `sort` | `string` | No | `"newest"` | Sorting algorithm: `newest`, `oldest`, `popular` (Weighted score: `views + 3*likes`), `most_liked` (`likes_count DESC`) |
| `page` | `integer` | No | `1` | Page number (min 1) |
| `limit` | `integer` | No | `20` | Items per page (min 1, max 100) |

#### Popularity Sorting Formula (`sort=popular`)
For `sort=popular`, the API computes an **Engagement Score** combining views and subscriber likes:
$$\text{Score} = \text{views\_count} + (3 \times \text{likes\_count})$$
This rewards high subscriber engagement, prevents clickbait videos from dominating the feed, and provides an enterprise-scale Netflix/Hotstar ranking.

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 101,
      "title": "Mastering Flutter & FastAPI Microservices",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
      "duration": 1200,
      "views_count": 14250,
      "category": "tutorials",
      "last_position_seconds": 480,
      "progress_percentage": 40.0,
      "published_at": "2026-08-05T10:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3
}
```

---

### 2. `GET /api/v1/mobile/videos/continue-watching` — Continue Watching Carousel Feed

Retrieves a paginated list of videos that **the authenticated subscriber has started watching but not completed yet**, sorted by most recently watched (`last_watched_at DESC`). Serves the "Continue Watching" carousel on the mobile home screen.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `page` | `integer` | No | `1` | Page number (min 1) |
| `limit` | `integer` | No | `10` | Items per page (min 1, max 50) |

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 101,
      "title": "Mastering Flutter & FastAPI Microservices",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
      "duration": 1200,
      "views_count": 14250,
      "category": "tutorials",
      "last_position_seconds": 425,
      "progress_percentage": 35.4,
      "published_at": "2026-08-05T10:00:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "limit": 10,
  "total_pages": 1
}
```

---

### 3. `GET /api/v1/mobile/videos/history` — Full Watch History Feed

Retrieves a paginated list of all videos watched by the authenticated subscriber, sorted by `last_watched_at DESC`.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 101,
      "title": "Mastering Flutter & FastAPI Microservices",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
      "duration": 1200,
      "views_count": 14250,
      "category": "tutorials",
      "last_position_seconds": 425,
      "progress_percentage": 35.4,
      "published_at": "2026-08-05T10:00:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

---

### 4. `DELETE /api/v1/mobile/videos/history` — Clear All Watch History

Clears the entire watch history for the authenticated subscriber.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success",
  "message": "Watch history cleared successfully"
}
```

---

### 5. `DELETE /api/v1/mobile/videos/history/{video_id}` — Remove Single Video from Watch History

Removes a specific video from the authenticated subscriber's watch history and "Continue Watching" carousel.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Path Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `video_id` | `integer` | Yes | Primary key ID of the video to remove from history |

#### Response Specification (`200 OK`)
```json
{
  "status": "success",
  "message": "Video removed from watch history"
}
```

---

### 6. `GET /api/v1/mobile/videos/liked` — My Liked Videos (Subscriber Favorites)

Retrieves a paginated list of videos that **the authenticated subscriber has liked**, sorted by `liked_at DESC`. Serves the "Liked Videos" screen in the mobile app profile.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 101,
      "title": "Mastering Flutter & FastAPI Microservices",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
      "duration": 1200,
      "views_count": 14250,
      "category": "tutorials",
      "last_position_seconds": 480,
      "progress_percentage": 40.0,
      "published_at": "2026-08-05T10:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

---

### 7. `GET /api/v1/mobile/videos/saved` — My Saved Videos (Subscriber Watchlist)

Retrieves a paginated list of videos that **the authenticated subscriber has saved / bookmarked**, sorted by `saved_at DESC`. Serves the "My Watchlist" screen in the mobile app profile.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 101,
      "title": "Mastering Flutter & FastAPI Microservices",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
      "duration": 1200,
      "views_count": 14250,
      "category": "tutorials",
      "last_position_seconds": 480,
      "progress_percentage": 40.0,
      "published_at": "2026-08-05T10:00:00Z"
    }
  ],
  "total": 5,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

---

### 8. `GET /api/v1/mobile/videos/{video_id}` — Video Details & Presigned HLS / MP4 Stream Player

Retrieves complete video metadata, **time-bound presigned HLS player URL** (`playlist.m3u8?token=...`), **presigned MP4 download links** for offline playback (filtered by available resolutions), dynamic `is_liked` & `is_saved` state, and **`last_position_seconds`** to resume playback.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required: Strictly requires subscriber role)
```

#### Response Specification (`200 OK`)
```json
{
  "id": 101,
  "title": "Mastering Flutter & FastAPI Microservices",
  "description": "Learn how to build high-performance video streaming mobile apps with adaptive bitrate HLS streaming and offline downloads.",
  "category": "tutorials",
  "tags": ["flutter", "fastapi", "hls", "ott"],
  "duration": 1200,
  "views_count": 14251,
  "likes_count": 1240,
  "is_liked": true,
  "is_saved": false,
  "last_position_seconds": 425,
  "progress_percentage": 35.4,
  "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
  "hls_stream_url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_9988/playlist.m3u8?token=a1b2c3d4e5f6...&expires=1786195200",
  "download_urls": [
    {
      "resolution": "1080p",
      "url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_9988/play_1080p.mp4?token=x1y2z3...&expires=1786195200"
    }
  ],
  "captions": [
    {
      "language": "English",
      "srclang": "en",
      "url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_9988/captions/en.vtt"
    }
  ],
  "published_at": "2026-08-05T10:00:00Z"
}
```

---

### 9. `POST /api/v1/mobile/videos/{video_id}/progress` — Sync Watch Progress Heartbeat

Syncs playback watch position from the mobile video player into `watch_history`.

#### Calling Schedule & Triggers (Mobile Client Rules)
To guarantee precise resume positioning and zero-trust view eligibility, the mobile player must dispatch this endpoint at four deterministic milestones:
1. **Playback Start**: Dispatched immediately upon video start/resume (`progress_seconds = 0` or initial resume second).
2. **Periodic Interval**: Dispatched every **10 seconds** during continuous streaming playback.
3. **30% Watch Threshold Trigger**: Dispatched the exact moment playback crosses **30% of video duration** ($0.30 \times \text{duration}$). Immediately after this sync completes, the mobile player calls `POST /api/v1/mobile/videos/{video_id}/views`.
4. **Lifecycle Events**: Dispatched on player pause, seek/scrub release, app backgrounding, screen exit (`dispose()`), or video completion ($\ge 95\%$).

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required: Strictly requires subscriber role)
```

#### Request Body
```json
{
  "progress_seconds": 18
}
```

#### Response Specification (`204 No Content`)
```http
HTTP/1.1 204 No Content
(Empty response body for maximum performance and zero network overhead)
```

---

### 10. `POST /api/v1/mobile/videos/{video_id}/views` — Increment View Count

Registers an immutable, verified watch view for creator analytics. Strictly verified on the backend (Zero-Trust Model).

#### Backend Verification Pipeline (Zero-Trust Security)
When this endpoint is invoked, the backend independently verifies four strict security and anti-spam gates before crediting a view:
1. **Subscriber Role Enforcement**: Caller must be an authenticated account with `role == 'subscriber'`. Anonymous guest accounts (`role == 'guest'`) are rejected with `HTTP 403 Forbidden` (`"Subscriber access required to record views"`).
2. **Backend Watch Progress Verification**: The backend queries `watch_history` for `(video_id, subscriber_id)` and independently validates that `last_position_seconds >= VIDEO_VIEW_WATCH_THRESHOLD_PERCENT` (default: `30.0%` of video duration). If the client has not actually streamed at least this threshold, the request is rejected with `HTTP 400 Bad Request` (`"WATCH_THRESHOLD_NOT_MET"`).
3. **Session Debounce Cooldown**: Checks `video_view_events` to ensure no view has been credited to this subscriber for this video within `VIDEO_VIEW_COOLDOWN_MINUTES` (default: `30` minutes). Replays within the cooldown window count as the same continuous viewing session.
4. **Daily View Cap**: Checks `video_view_events` to ensure this subscriber has not exceeded `VIDEO_VIEW_MAX_DAILY_PER_USER` (default: `3` views) for this video within a rolling `VIDEO_VIEW_DAILY_WINDOW_HOURS` (default: `24` hours), preventing loop and bot manipulation.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required: Strictly requires subscriber role)
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success",
  "views_count": 14252
}
```

---

### 11. `POST /api/v1/mobile/videos/{video_id}/like` — Toggle Subscriber Video Like

Toggles like state (like / unlike) for an authenticated subscriber on a published video asset.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Response Specification (`200 OK`)
```json
{
  "is_liked": true,
  "likes_count": 1241
}
```

---

### 12. `POST /api/v1/mobile/videos/{video_id}/save` — Toggle Subscriber Video Save (Watchlist)

Toggles saved/bookmarked state (save / unsave) for an authenticated subscriber on a published video asset.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Response Specification (`200 OK`)
```json
{
  "is_saved": true
}
```

---

## 📱 Mobile Video Player Integration Guidelines

1. **Adaptive Bitrate Playback (HLS)**:
   - Use native video player engines (`better_player` / `chewie` / `video_player` in Flutter, `react-native-video` in React Native, `AVPlayer` on iOS, `ExoPlayer` on Android).
   - Pass `hls_stream_url` directly to player. The player will automatically adapt resolution based on network speed (1080p ➔ 720p ➔ 480p).
2. **Automatic Resume Playback**:
   - On video screen load, inspect `last_position_seconds` returned by `GET /api/v1/mobile/videos/{video_id}`.
   - Seek video player to `last_position_seconds` automatically before playing!
3. **Playback Sync Timer**:
   - Set a 10-second timer inside your video player controller to call `POST /api/v1/mobile/videos/{video_id}/progress` with current playback seconds.
4. **Presigned Token Security**:
   - Presigned playback URLs (`playlist.m3u8?token=...&expires=...`) expire after `BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS` (2 hours).
   - If user pauses playback for over 2 hours, fetch fresh details via `GET /api/v1/mobile/videos/{video_id}`.
