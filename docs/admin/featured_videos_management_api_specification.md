# Admin Featured Videos Management API Specification

This document details the RESTful API endpoints for Web Admin Creators to manage, feature, order, and curate featured videos displayed on the mobile application home screen hero carousel.

---

## 1. Architecture & Design Principles

* **Base Prefix**: `/api/v1/admin/featured-videos`
* **Authentication**: **Admin Creator Protected** (`Authorization: Bearer <admin_access_token>`).
* **Multi-Tenant Isolation**: Extracted `current_user["user_id"]` from JWT context guarantees creators can only feature, reorder, or delete their own videos.
* **Ordering Model**: Dedicated `featured_videos` table maintains 1-indexed `position` attributes supporting drag-and-drop reordering.
* **Maximum Cap**: Up to **10 featured videos** can be active per creator studio at a time.
* **IDOR Protection**: All mutations validate `Video.user == current_user["user_id"]`.

---

## 2. API Endpoints Overview

| Method | Endpoint Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/admin/featured-videos` | List all featured videos with current ordering positions |
| `POST` | `/api/v1/admin/featured-videos` | Add video(s) to the featured list |
| `PUT` | `/api/v1/admin/featured-videos/reorder` | Batch reorder featured video positions |
| `DELETE` | `/api/v1/admin/featured-videos` | Bulk remove selected videos from the featured list |
| `DELETE` | `/api/v1/admin/featured-videos/{video_id}` | Remove a single video from the featured list |
| `GET` | `/api/v1/admin/featured-videos/available` | List creator videos available to be featured (picker with sort) |

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

### 3.2 `POST /api/v1/admin/featured-videos`

Adds one or more creator video IDs to the featured list. Appends new items at the next available `position`.

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Payload
```json
{
  "video_ids": [45, 48]
}
```

#### Response Envelope (`201 Created`)
```json
{
  "status": "success",
  "added_count": 2,
  "total_featured": 5
}
```

#### Error Envelopes
* **`400 Bad Request`** (Cap Limit Exceeded):
  ```json
  {
    "detail": "Cannot exceed maximum of 10 featured videos. Currently featured: 9."
  }
  ```
* **`404 Not Found`** (Video Not Found / Unauthorized):
  ```json
  {
    "detail": "Video 99 not found or does not belong to creator."
  }
  ```

---

### 3.3 `PUT /api/v1/admin/featured-videos/reorder`

Reorders featured video positions using a batch sequence of video IDs matching the desired visual order.

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Payload
```json
{
  "video_ids": [48, 45]
}
```

#### Response Envelope (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 3.4 `DELETE /api/v1/admin/featured-videos`

Bulk removes multiple selected videos from the creator's featured list and automatically re-compacts position sequence.

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Payload
```json
{
  "video_ids": [45, 48]
}
```

#### Response Envelope (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 3.5 `DELETE /api/v1/admin/featured-videos/{video_id}`

Removes a single video from the featured list and automatically adjusts remaining positions (`position - 1`).

#### Headers
```http
Authorization: Bearer <admin_access_token>
```

#### Response Envelope (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 3.6 `GET /api/v1/admin/featured-videos/available`

Retrieves a paginated list of published creator videos that are **not** currently in the featured list (used by video picker modals in the admin panel). Supports sorting by newest, oldest, popular (most viewed), and most liked.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `search` | `string` | No | `null` | Substring search within video titles |
| `category` | `string` | No | `null` | Filter by category slug |
| `sort` | `string` | No | `newest` | Sort criteria: `newest`, `oldest`, `popular` (or `most_viewed`), `most_liked` |
| `page` | `integer` | No | `1` | Page number |
| `limit` | `integer` | No | `20` | Items per page (max 100) |

#### Response Envelope (`200 OK`)
```json
{
  "total": 15,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
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
