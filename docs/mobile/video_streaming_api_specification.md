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

1. **`GET /api/v1/mobile/videos` (Standard Catalog Feed & Search)**:
   - **Guarded by**: `Depends(get_current_subscriber)`
   - **Header**: `Authorization: Bearer <access_token>` (**Required**)
   - **Multi-Tenant Isolation**: Decodes `current_subscriber["tenant_id"]` from JWT claims (< 1ms) and filters catalog queries (`Video.select().where(Video.tenant == tenant_id, Video.video_type == 'standard')`).
   - **Allowed Roles**: Both `guest` AND `subscriber`
   - **Behavior**: Rejects requests missing a Bearer token with `HTTP 401 Unauthorized`. Accepts Guest tokens for catalog browsing, and Subscriber tokens for browsing + personalized progress.

2. **`GET /api/v1/mobile/videos/shorts` (Vertical Reels / Shorts Swipe Feed)**:
   - **Guarded by**: `Depends(get_current_subscriber)`
   - **Header**: `Authorization: Bearer <access_token>` (**Required**)
   - **Multi-Tenant Isolation**: Filters by tenant and strictly `video_type == 'shorts'`.
   - **Allowed Roles**: Both `guest` AND `subscriber`
   - **Behavior**: Bundles presigned HLS and direct MP4 URLs, poster thumbnail, engagement metrics, creator branding, and personalized `is_liked` / `is_saved` state for instant vertical swiping.

3. **`GET /api/v1/mobile/videos/{video_id}` (Video Player & HLS Stream)**:
   - **Guarded by**: `Depends(get_current_subscriber)`
   - **Header**: `Authorization: Bearer <access_token>` (**Required**)
   - **Allowed Roles**: Strictly `subscriber` (and creator/admin)
   - **Behavior**: Blocks Guest accounts with `HTTP 403 Forbidden` (`"Subscriber access required"`). Forces Guests to sign in with Google or Facebook to stream videos!

4. **Protected Subscriber Actions**:
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
     - `POST /api/v1/mobile/videos/{id}/ad-impression` *(Record In-Stream Ad Impression Telemetry)*
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

### 2. `GET /api/v1/mobile/videos/shorts` — Vertical Short Videos (Reels / Shorts) Swipe Feed

Retrieves a paginated list of published, ready-to-stream **short vertical video assets** (Instagram Reels / YouTube Shorts style).

#### ⚡ Zero-Latency Full-Screen Player Architecture
Unlike standard catalog endpoints (`GET /api/v1/mobile/videos`) which return metadata cards without media streams (requiring a second call to `/videos/{id}`), the Shorts feed **directly bundles presigned adaptive HLS streams (`hls_stream_url`)** alongside creator branding, caption tracks, and interaction counters (`likes_count`, `comments_count`, `is_liked`, `is_saved`).

This architecture allows mobile video players (Flutter `PageView.builder`, React Native `FlatList`, iOS `UICollectionView`) to preload the next 2-3 vertical videos into memory and begin rendering on swipe with **0ms playback latency** and continuous looping.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required: Accepts Guest token for public preview, Subscriber token for full personalized playback & interactions)
```

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `page` | `integer` | No | `1` | Page number for cursor/infinite scrolling (min 1) |
| `limit` | `integer` | No | `10` | Number of shorts per batch (min 1, max 20, default 10) |
| `sort` | `string` | No | `"newest"` | Sorting algorithm: `newest` (recent uploads first), `popular` (weighted engagement: `views + 3*likes`), `most_liked` |

#### 🔒 Content Isolation, Ad-Free, No Downloads & No Categories Guarantee
- **Shorts Feed (`/videos/shorts`)**: Exclusively returns videos where `video_type = 'shorts'` and `status = 'published'` and `transcoding_status = 'READY'`.
- **Standard Catalog Feed (`/videos`)**: Exclusively returns standard widescreen/landscape videos (`video_type = 'standard'`), ensuring vertical micro-content never pollutes movie, series, or tutorial carousels.
- **🚫 No Categories**: Vertical short videos have no category (`category` is strictly `null`). The shorts feed operates purely as an algorithmic/chronological vertical swipe stream (`sort: newest | popular`). Categories are strictly reserved for standard long-form catalog videos.
- **🚫 100% Ad-Free Experience**: Vertical short videos are strictly ad-free (`ad_tag_url` is omitted). Google IMA VAST video ads are never inserted into the Shorts swipe experience, guaranteeing continuous, uninterrupted looping.
- **🔒 No Downloads / HLS-Only**: Short videos are strictly for in-app online swipe streaming via adaptive HLS (`hls_stream_url`). Offline MP4 downloads are disabled for shorts to safeguard creator content.

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 201,
      "title": "Clean Architecture in 60 Seconds 🚀",
      "description": "Why separating routes, services, and repositories saves months of refactoring.",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_201_main.jpg",
      "duration": 58,
      "views_count": 14200,
      "likes_count": 1820,
      "comments_count": 94,
      "is_liked": true,
      "is_saved": false,
      "hls_stream_url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_5544/playlist.m3u8?token=a1b2c3d4e5f6...&expires=1786195200",
      "captions": [
        {
          "language": "English",
          "srclang": "en-auto",
          "url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_5544/captions/en-auto.vtt"
        }
      ],
      "creator": {
        "name": "Alex Rivers",
        "logo_url": "https://talentsea.b-cdn.net/branding/logo.png"
      },
      "published_at": "2026-09-22T16:00:00Z"
    }
  ],
  "total": 35,
  "page": 1,
  "limit": 10,
  "total_pages": 4
}
```

#### 🔄 Zero-Redundancy Social Interactions for Shorts
Because shorts are unified within the core `videos` entity, **all social and engagement actions reuse the existing video endpoints directly**:
- **Like / Unlike a Short**: `POST /api/v1/mobile/videos/{id}/like`
- **Save / Bookmark a Short**: `POST /api/v1/mobile/videos/{id}/save`
- **View Comments on a Short**: `GET /api/v1/mobile/comments?video_id={id}`
- **Post a Comment on a Short**: `POST /api/v1/mobile/comments` with `{ "video_id": 201, "content": "..." }`
- **Increment View Count**: `POST /api/v1/mobile/videos/{id}/views`
- **Watch Progress Tracking**: `POST /api/v1/mobile/videos/{id}/progress`

---

### 3. `GET /api/v1/mobile/videos/continue-watching` — Continue Watching Carousel Feed

Retrieves a paginated list of videos that **the authenticated subscriber has started watching but not completed yet**, sorted by most recently watched (`last_watched_at DESC`). Serves the "Continue Watching" carousel on the mobile home screen.

> [!NOTE]
> **Strict Exclusion of Shorts:** This endpoint strictly filters `WHERE video_type == 'standard'`. Vertical short videos (15-60s looping micro-content) are **excluded** from Continue Watching so the home screen carousel stays exclusively focused on movies, series episodes, and tutorials.

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

### 4. `GET /api/v1/mobile/videos/history` — Full Watch History Feed

Retrieves a paginated list of all videos watched by the authenticated subscriber, sorted by `last_watched_at DESC`.

> [!NOTE]
> **Full History Includes Shorts:** Unlike the Continue Watching carousel, the complete Watch History feed **includes both standard catalog videos and vertical short videos** (`video_type IN ('standard', 'shorts')`), giving subscribers a complete chronological log of all content they have engaged with.

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

### 5. `DELETE /api/v1/mobile/videos/history` — Clear All Watch History

Clears the entire watch history for the authenticated subscriber.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 6. `DELETE /api/v1/mobile/videos/history/{video_id}` — Remove Single Video from Watch History

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
  "status": "success"
}
```

---

### 7. `GET /api/v1/mobile/videos/liked` — My Liked Videos (Subscriber Favorites)

Retrieves a paginated list of videos that **the authenticated subscriber has liked**, sorted by `liked_at DESC`. Serves the "Liked Videos" screen in the mobile app profile. Supports filtering specifically for shorts or standard videos.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `video_type` | `string` | No | `null` | Filter liked items by video type: `'shorts'` or `'standard'`. Omit to return all. |
| `page` | `integer` | No | `1` | Page number ($\ge 1$). |
| `limit` | `integer` | No | `20` | Items per page ($1 \le \text{limit} \le 100$). |

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
      "video_type": "standard",
      "last_position_seconds": 480,
      "progress_percentage": 40.0,
      "published_at": "2026-08-05T10:00:00Z"
    },
    {
      "id": 105,
      "title": "Exciting Behind The Scenes",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_105_main.jpg",
      "duration": 45,
      "views_count": 3200,
      "category": null,
      "video_type": "shorts",
      "last_position_seconds": 0,
      "progress_percentage": 0.0,
      "published_at": "2026-08-06T12:00:00Z"
    }
  ],
  "total": 12,
  "page": 1,
  "limit": 20,
  "total_pages": 1
}
```

---

### 8. `GET /api/v1/mobile/videos/saved` — My Saved Videos (Subscriber Watchlist)

Retrieves a paginated list of videos that **the authenticated subscriber has saved / bookmarked**, sorted by `saved_at DESC`. Serves the "My Watchlist" screen in the mobile app profile. Supports filtering specifically for saved shorts or saved standard videos.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required)
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `video_type` | `string` | No | `null` | Filter saved items by video type: `'shorts'` or `'standard'`. Omit to return all. |
| `page` | `integer` | No | `1` | Page number ($\ge 1$). |
| `limit` | `integer` | No | `20` | Items per page ($1 \le \text{limit} \le 100$). |

#### Examples:
- **Get Only Saved Shorts**: `GET /api/v1/mobile/videos/saved?video_type=shorts`
- **Get Only Saved Standard Videos**: `GET /api/v1/mobile/videos/saved?video_type=standard`
- **Get All Saved Videos & Shorts**: `GET /api/v1/mobile/videos/saved`

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 105,
      "title": "Exciting Behind The Scenes",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_105_main.jpg",
      "duration": 45,
      "views_count": 3200,
      "category": null,
      "video_type": "shorts",
      "last_position_seconds": 0,
      "progress_percentage": 0.0,
      "published_at": "2026-08-06T12:00:00Z"
    },
    {
      "id": 101,
      "title": "Mastering Flutter & FastAPI Microservices",
      "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
      "duration": 1200,
      "views_count": 14250,
      "category": "tutorials",
      "video_type": "standard",
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

### 9. `GET /api/v1/mobile/videos/{video_id}` — Video Details & Presigned HLS / MP4 Stream Player

Retrieves complete video metadata. If the authenticated user holds an active subscription under this creator studio, it attaches the **time-bound presigned HLS player URL** (`playlist.m3u8?token=...`), **presigned MP4 download links** (for standard videos), and **closed caption tracks**. 

If the user is **unsubscribed or expired**, all protected media assets (`hls_stream_url`, `download_urls`, `captions`, and `ad_tag_url`) are strictly set to `null`, enabling the mobile app to render a high-converting **"Subscribe to Watch"** preview screen while safeguarding proprietary content.

If the requested video is a **vertical Short video (`video_type == "shorts"`)**, the endpoint dynamically enforces shorts guardrails: **`download_urls` is strictly `null`** (shorts are 100% streaming-only) and **`ad_tag_url` is strictly `null`** (shorts are 100% ad-free across all subscription tiers).

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required: Accepts subscriber or guest token)
```

#### 🛡️ Playback Entitlement & Asset Security Matrix

| Field in Response | 🚫 Unsubscribed / Free User | 🍿 Standard Tier (`with_ads`) — Standard Video | 💎 Premium Tier (`no_ads`) — Standard Video | ⚡ Any Active Tier — Short Video (`video_type = 'shorts'`) |
| :--- | :---: | :---: | :---: | :---: |
| **`video_type`** | `"standard"` or `"shorts"` | `"standard"` | `"standard"` | `"shorts"` |
| **Metadata (`title`, `thumbnail_url`, etc.)** | ✅ Included | ✅ Included | ✅ Included | ✅ Included |
| **`hls_stream_url`** | ❌ **`null`** (Locked) | ✅ **Presigned HLS URL** | ✅ **Presigned HLS URL** | ✅ **Presigned HLS URL** |
| **`download_urls`** | ❌ **`null`** (Locked) | ✅ **Presigned MP4 URLs** | ✅ **Presigned MP4 URLs** | ❌ **`null`** (Streaming-Only) |
| **`captions`** | ❌ **`null`** (Locked) | ✅ **VTT Caption Tracks** | ✅ **VTT Caption Tracks** | ✅ **VTT Tracks** (if present) |
| **`ad_tag_url`** | ❌ **`null`** (No Content Stream) | ✅ **VAST / VMAP Ad Tag** | ❌ **`null`** (Ad-Free) | ❌ **`null`** (100% Ad-Free) |

---

#### 💡 Architectural Rationale: Protected Assets, Ad Delivery & Shorts Guardrails

1. **Why `captions` is `null` for unsubscribed users:**
   - Closed caption (`.vtt`) files contain the full verbatim transcript of the video. Exposing captions to unsubscribed users allows automated scraping and theft of proprietary video scripts and educational course content. Setting `captions: null` protects intellectual property.

2. **Why `download_urls` is `null` for unsubscribed users:**
   - Offline MP4 downloads are exclusively available to active subscribers. Setting `download_urls: null` ensures no direct raw video files can be retrieved or reverse-engineered by unsubscribed clients.

3. **Why `ad_tag_url` is `null` for unsubscribed users:**
   - **Google Ad Manager / IAB Policy Compliance:** VAST/VMAP video ads are in-stream formats that require an active content stream. Firing video ads on a locked screen without playable content produces phantom impressions and 0% viewability, which violates Google Ad Manager terms and risks creator/platform account penalization for invalid traffic.
   - **Monetization & Conversion Funnel:** In-stream ads monetize users who selected the lower-priced **Standard (`with_ads`)** subscription. Unsubscribed users should not see third-party commercial ads; their user journey must be 100% focused on subscribing via the high-converting in-app paywall.
   - **Client Performance:** Prevents the mobile client from needlessly initializing the Google IMA SDK container or consuming network bandwidth on preview screens.

4. **Why `download_urls` and `ad_tag_url` are `null` for Short Videos (`video_type == "shorts"`):**
   - **No Offline MP4 Downloads (`download_urls: null`):** Short vertical videos are designed for immediate, fast-swiping inline streaming. Disabling MP4 downloads conserves Bunny CDN egress and enforces cloud playback fidelity.
   - **100% Ad-Free Guarantee (`ad_tag_url: null`):** Micro-content reel UX requires instant, zero-latency looping. In-stream VAST video ads are never inserted into shorts, even when the user is subscribed under an ad-supported plan (`with_ads`).

---

#### Response Specifications (`200 OK`)

##### Response A: Unsubscribed User (Playback Locked — Show "Subscribe to Watch")
```json
{
  "id": 101,
  "title": "Mastering Flutter & FastAPI Microservices",
  "description": "Learn how to build high-performance video streaming mobile apps with adaptive bitrate HLS streaming and offline downloads.",
  "category": "tutorials",
  "video_type": "standard",
  "tags": ["flutter", "fastapi", "hls", "ott"],
  "duration": 1200,
  "views_count": 14251,
  "likes_count": 1240,
  "is_liked": false,
  "is_saved": false,
  "last_position_seconds": 0,
  "progress_percentage": 0.0,
  "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_101_main.jpg",
  "hls_stream_url": null,
  "download_urls": null,
  "captions": null,
  "ad_tag_url": null,
  "published_at": "2026-08-05T10:00:00Z"
}
```

##### Response B: Standard Subscriber (`plan_type = "with_ads"`) — Standard Video
```json
{
  "id": 101,
  "title": "Mastering Flutter & FastAPI Microservices",
  "description": "Learn how to build high-performance video streaming mobile apps with adaptive bitrate HLS streaming and offline downloads.",
  "category": "tutorials",
  "video_type": "standard",
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
      "resolution": "720p",
      "url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_9988/play_720p.mp4?token=x1y2z3...&expires=1786195200"
    }
  ],
  "captions": [
    {
      "language": "English",
      "srclang": "en",
      "url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_9988/captions/en.vtt"
    }
  ],
  "ad_tag_url": "https://pubads.g.doubleclick.net/gampad/ads?iu=/21775744923/external/single_preroll_skippable&sz=640x480&ciu_szs=300x250%2C728x90&gdfp_req=1&output=vast&unviewed_position_start=1&env=vp&impl=s&correlator=",
  "published_at": "2026-08-05T10:00:00Z"
}
```

##### Response C: Premium Subscriber (`plan_type = "no_ads"`) — Standard Video
```json
{
  "id": 101,
  "title": "Mastering Flutter & FastAPI Microservices",
  "description": "Learn how to build high-performance video streaming mobile apps with adaptive bitrate HLS streaming and offline downloads.",
  "category": "tutorials",
  "video_type": "standard",
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
  "ad_tag_url": null,
  "published_at": "2026-08-05T10:00:00Z"
}
```

##### Response D: Active Subscriber Playing a Short Video (`video_type = "shorts"`)
```json
{
  "id": 205,
  "title": "Quick CSS Tip: Responsive Grids in 30 Seconds",
  "description": "Master CSS grid auto-fit minmax in under a minute!",
  "category": null,
  "video_type": "shorts",
  "tags": ["css", "frontend", "shorts"],
  "duration": 35,
  "views_count": 8940,
  "likes_count": 920,
  "is_liked": true,
  "is_saved": false,
  "last_position_seconds": 0,
  "progress_percentage": 0.0,
  "thumbnail_url": "https://talentsea.b-cdn.net/thumbnails/thumb_205_main.jpg",
  "hls_stream_url": "https://vz-b9ac573c-27c.b-cdn.net/bunny_vid_1122/playlist.m3u8?token=s1s2s3...&expires=1786195200",
  "download_urls": null,
  "captions": null,
  "ad_tag_url": null,
  "published_at": "2026-08-10T14:00:00Z"
}
```

---

#### 📱 Mobile App Player Implementation (Client Logic)

Mobile developers (Flutter, React Native, iOS, Android) use a clean entitlement check and player routing:

```dart
if (video.hls_stream_url != null) {
  // 1. User holds an active subscription
  if (video.video_type == "shorts") {
    // ⚡ Short Video: Launch vertical swipe reel player (100% ad-free, streaming-only)
    player.playVerticalShort(video.hls_stream_url);
  } else {
    // 🎬 Standard Video: Launch landscape 16:9 player
    if (video.ad_tag_url != null) {
      // Standard Tier: Initialize Google IMA SDK with VAST/VMAP URL
      player.playWithAds(video.hls_stream_url, adTag: video.ad_tag_url);
    } else {
      // Premium Tier: Stream directly with zero ads
      player.playDirect(video.hls_stream_url);
    }
  }

  // Attach closed captions if available
  if (video.captions != null && video.captions.isNotEmpty) {
    player.setSubtitles(video.captions);
  }
} else {
  // 2. User is unsubscribed or expired: Render locked preview
  // Protected media assets (hls_stream_url, download_urls, captions, ad_tag_url) are all null
  showSubscribeToWatchOverlay(
    thumbnailUrl: video.thumbnail_url,
    title: video.title,
    onSubscribeTap: () => navigateToSubscriptionPlans(),
  );
}
```

---

### 10. `POST /api/v1/mobile/videos/{video_id}/progress` — Sync Watch Progress Heartbeat

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

### 11. `POST /api/v1/mobile/videos/{video_id}/views` — Increment View Count

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

### 12. `POST /api/v1/mobile/videos/{video_id}/like` — Toggle Subscriber Video Like

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

### 13. `POST /api/v1/mobile/videos/{video_id}/save` — Toggle Subscriber Video Save (Watchlist)

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

### 14. `POST /api/v1/mobile/videos/{video_id}/ad-impression` — Record In-Stream Ad Impression Telemetry

Dispatched by the mobile video player whenever the **Google Interactive Media Ads (IMA) SDK** fires an ad impression or milestone event during video playback on the Standard tier (`with_ads`).

Logs an immutable, verified ad impression in the backend telemetry engine (`ad_impression_events`), powering real-time Creator Studio ad analytics, fill rate reporting, and monthly revenue settlement calculations.

#### Calling Schedule & Triggers (Mobile Client Rules)
1. **The Primary Trigger (`AdEvent.IMPRESSION`):**
   - Dispatched the exact moment Google IMA SDK fires `AdEventType.IMPRESSION` (automatically triggered at the **2-second** mark of continuous viewable playback).
   - This single API call officially marks the ad as counted/monetized in the creator's monthly revenue ledger.
2. **Single Call Per Ad (No Double Counting):**
   - The mobile app calls this endpoint **only once per ad**.
3. **What Happens on Skip? (`AdEvent.SKIPPED`):**
   - Skippable ads have a mandatory 5-second countdown before the user can click "Skip".
   - Because the 2-second impression was already recorded at second 2, **the impression is already monetized**. If the user clicks "Skip" at second 5, the client simply transitions to the content video and does **not** make another API call.
4. **Early App Exit (< 2 seconds):**
   - If the user closes the app or navigates away before reaching 2 seconds, Google IMA SDK never fires `AdEventType.IMPRESSION`, and the mobile app must **not** call this endpoint.

#### Request Headers
```http
Authorization: Bearer <access_token>  (Required: Strictly requires active subscriber role)
Content-Type: application/json
```

#### Path Parameters
| Parameter | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `video_id` | `integer` | Yes | Primary key ID of the video currently playing the ad |

#### Request Body
```json
{
  "event_type": "impression",
  "ad_duration_seconds": 15
}
```

#### Request Payload Validation Rules
- `event_type`: Required string. Allowed values:
  - `"impression"`: Ad has successfully started rendering and passed the 2-second IAB viewability mark.
  - `"midpoint"`: Ad playback reached 50% duration.
  - `"complete"`: Ad played to completion without being skipped.
- `ad_duration_seconds`: Optional integer (default: `0`). Creative duration in seconds.

#### Response Specification (`204 No Content`)
```http
HTTP/1.1 204 No Content
(Empty response body for maximum performance and zero network overhead on mobile cellular connections)
```

#### 🛡️ Zero-Trust Verification & Anti-Spam Debounce Gates
When this endpoint is invoked, the backend enforces 5 zero-trust validation checks:
1. **Subscriber Role Enforcement:** Anonymous guest accounts are rejected with `HTTP 403 Forbidden` (`"Subscriber access required to log ad telemetry"`).
2. **Active Subscription Verification:** Validates that caller holds an active subscription with `plan_type == 'with_ads'`. If caller holds a `no_ads` Premium subscription or is unsubscribed, request is rejected.
3. **Published Video Validation:** Video must exist, be published, and belong to the calling tenant's creator studio.
4. **Standard Video Content Enforcement:** In-stream ad impressions are **strictly valid for standard catalog videos** (`video_type == 'standard'`). Short videos (`video_type == 'shorts'`) are 100% ad-free and reject ad impression events.
5. **Session Debounce Cooldown:** If multiple impression pings arrive for the same `(subscriber_id, video_id)` within `10 seconds`, duplicate pings are discarded to prevent client loop or replay attacks.

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
