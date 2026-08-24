# Admin Featured Videos Management API Specification

This document details the RESTful API endpoints for Web Admin Creators to manage, feature, order, and curate featured videos displayed on the mobile application home screen hero carousel.

---

## 1. Architecture & Design Principles

* **Base Prefix**: `/api/v1/admin/featured-videos`
* **Authentication**: **Admin Creator Protected** (`Authorization: Bearer <admin_access_token>`).
* **Multi-Tenant Isolation**: Extracted `current_user["user_id"]` from JWT context guarantees creators can only feature, reorder, or delete their own videos.
* **Full State Sync Pattern (`PUT`)**: A single `PUT` endpoint handles adding, reordering, single deletion, and bulk deletion by receiving the complete ordered array of active featured `video_ids`.
* **Ordering Model**: Dedicated `featured_videos` table maintains 1-indexed `position` attributes corresponding to the index order in the request payload (`position = index + 1`).
* **Maximum Cap**: Up to **10 featured videos** can be active per creator studio at a time (`MAX_FEATURED_VIDEOS_PER_CREATOR`).
* **IDOR Protection**: All state updates validate `Video.user == current_user["user_id"]`.

---

## 2. API Endpoints Overview

| Method | Endpoint Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/admin/featured-videos` | List all featured videos with current ordering positions |
| `PUT` | `/api/v1/admin/featured-videos` | Full State Sync (Add, Reorder, Single Delete, and Bulk Delete in 1 API) |
| `GET` | `/api/v1/admin/featured-videos/available` | List creator videos available to be featured (picker modal with sort & search) |

---

## 3. Detailed Endpoint Specifications

### 3.1 `GET /api/v1/admin/featured-videos`

Retrieves all videos currently featured by the authenticated creator, ordered by `position` ascending.

#### Headers
```http
Authorization: Bearer <admin_access_token>
```

#### Response Envelope (`200 OK`)
```json
[
  {
    "id": 12,
    "video_id": 45,
    "position": 1,
    "title": "Introduction to Clean Architecture in FastAPI",
    "description": "Learn how to build production-grade FastAPI applications using 5-layer clean architecture.",
    "category": "Backend Development",
    "main_thumbnail_url": "https://talentsea77999.b-cdn.net/thumbnails/v45_slot0.jpg",
    "duration": "14:20",
    "views": 1420,
    "likes": 88,
    "status": "published",
    "created_at": "2026-08-20T10:00:00Z"
  },
  {
    "id": 13,
    "video_id": 48,
    "position": 2,
    "title": "Mastering Bunny Stream & TUS Uploads",
    "description": "Deep dive into HMAC signed TUS resumable uploads and HLS token security.",
    "category": "Video Engineering",
    "main_thumbnail_url": "https://talentsea77999.b-cdn.net/thumbnails/v48_slot0.jpg",
    "duration": "22:15",
    "views": 950,
    "likes": 64,
    "status": "published",
    "created_at": "2026-08-21T12:30:00Z"
  }
]
```

---

### 3.2 `PUT /api/v1/admin/featured-videos` — Full State Sync

Replaces and synchronizes the active featured videos list for the authenticated creator. 
This single endpoint performs all mutation operations:
* ➕ **Add Video(s)**: Include new video ID(s) in `video_ids`.
* ↕️ **Reorder Videos**: Arrange array sequence in the exact desired carousel display order.
* ❌ **Single / Bulk Delete**: Exclude video ID(s) from `video_ids`.

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Payload
```json
{
  "video_ids": [45, 48, 12, 88]
}
```

#### Payload Rules & Validations:
1. Max cap validation (`len(video_ids) <= 10`). Returns `400 Bad Request` if payload exceeds 10 items.
2. Ownership validation: Excludes invalid or unowned `video_ids` automatically.
3. Empty list supported: Passing `{"video_ids": []}` clears all featured videos for the creator.

#### Response Envelope (`200 OK`)
```json
{
  "status": "success",
  "total_featured": 2,
  "items": [
    {
      "id": 12,
      "video_id": 45,
      "position": 1,
      "title": "Introduction to Clean Architecture in FastAPI",
      "description": "Learn how to build production-grade FastAPI applications using 5-layer clean architecture.",
      "category": "Backend Development",
      "main_thumbnail_url": "https://talentsea77999.b-cdn.net/thumbnails/v45_slot0.jpg",
      "duration": "14:20",
      "views": 1420,
      "likes": 88,
      "status": "published",
      "created_at": "2026-08-20T10:00:00Z"
    },
    {
      "id": 13,
      "video_id": 48,
      "position": 2,
      "title": "Mastering Bunny Stream & TUS Uploads",
      "description": "Deep dive into HMAC signed TUS resumable uploads and HLS token security.",
      "category": "Video Engineering",
      "main_thumbnail_url": "https://talentsea77999.b-cdn.net/thumbnails/v48_slot0.jpg",
      "duration": "22:15",
      "views": 950,
      "likes": 64,
      "status": "published",
      "created_at": "2026-08-21T12:30:00Z"
    }
  ]
}
```

---

### 3.3 `GET /api/v1/admin/featured-videos/available` — Get Available Videos Picker

Retrieves a paginated list of creator's published videos that are **not currently featured**, used for populating the "Select Videos to Feature" picker modal.

#### Headers
```http
Authorization: Bearer <admin_access_token>
```

#### Query Parameters
- `search` (string, optional): Filter by title substring.
- `category` (string, optional): Filter by category slug/name.
- `sort` (string, optional, default: `"popular"`): Sort ordering (`"popular"`, `"most_viewed"`, `"oldest"`, `"newest"`).
  * `"popular"`: Sorts by indexed `popularity_score DESC` (`views + 3*likes`).
  * `"most_viewed"`: Sorts by `views DESC`.
  * `"oldest"`: Sorts by `created_at ASC`.
  * `"newest"`: Sorts by `created_at DESC`.
- `page` (integer, optional, default: `1`): Page number.
- `limit` (integer, optional, default: `20`, max: `100`): Items per page.

#### Example Request URL
```http
GET /api/v1/admin/featured-videos/available?sort=popular&page=1&limit=20
```

#### Response Envelope (`200 OK`)
```json
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3,
  "items": [
    {
      "id": 52,
      "title": "Building Real-Time OTT Applications",
      "category": "Architecture",
      "duration": "18:45",
      "main_thumbnail_url": "https://talentsea77999.b-cdn.net/thumbnails/v52_slot0.jpg",
      "views": 410,
      "likes": 32,
      "created_at": "2026-08-22T08:15:00Z"
    }
  ]
}
```
