# Mobile Playlist Feed & Video Streaming API Specification

## 1. Domain Overview & Architectural Guidelines

The **Mobile Playlist Feed API** powers curated video series, collections, and course playlists for mobile subscribers across iOS and Android apps. It allows mobile users to discover public creator playlists, view playlist details, and stream videos in ordered sequence with personalized watch progress, like states, and bookmarking.

### Key Technical Rules:
1. **Public & Subscriber Authentication**: Endpoints support both Guest Users (unauthenticated) and Logged-in Subscribers (`get_optional_subscriber`).
2. **Read-Only Access**: Mobile clients consume public creator playlists. Playlist creation, editing, thumbnail uploads, and video reordering are managed exclusively via Creator Admin APIs.
3. **Only Playable & Published Videos**: Playlist video feeds strictly include videos with `status == "published"` and `transcoding_status == "READY"`. Unready or draft videos are hidden.
4. **Personalized Subscriber Overlay**: For authenticated subscribers, responses include `is_liked`, `is_saved`, and `watch_progress` (`last_position_seconds`, `completion_percentage`). For guest users, these default to `false` / `null`.

---

## 2. API Endpoints Specification

### 1. `GET /api/v1/mobile/playlists` — List Public Playlists Feed

Retrieves a paginated list of public creator playlists for the mobile home screen or playlists discovery tab.

#### Request Headers
```http
Authorization: Bearer <optional_subscriber_access_token>
```
*(Optional: Guest users omit the `Authorization` header)*

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `search` | string | No | `null` | Filters playlists by name substring |
| `sort` | string | No | `"newest"` | Sort order: `newest`, `oldest`, `title` |
| `page` | integer | No | `1` | Page index (minimum `1`) |
| `limit` | integer | No | `20` | Items per page (minimum `1`, maximum `100`) |

#### Response Specification (`200 OK`)
```json
{
  "total": 5,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 104,
      "name": "Trending Sci-Fi Series",
      "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
      "video_count": 12,
      "created_at": "2024-05-01T00:00:00Z"
    },
    {
      "id": 102,
      "name": "FastAPI Masterclass 2026",
      "thumbnail_url": null,
      "video_count": 8,
      "created_at": "2024-04-15T00:00:00Z"
    }
  ]
}
```

---

### 2. `GET /api/v1/mobile/playlists/{playlist_id}` — Get Playlist Details & Video Feed

Retrieves playlist header details alongside the ordered list of published videos inside that playlist, populated with personalized watch progress and engagement state.

#### Request Headers
```http
Authorization: Bearer <optional_subscriber_access_token>
```
*(Optional: Guest users omit the `Authorization` header)*

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the target playlist.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `page` | integer | No | `1` | Page index for playlist videos (minimum `1`) |
| `limit` | integer | No | `20` | Video items per page (minimum `1`, maximum `100`) |

#### Response Specification (`200 OK`)
```json
{
  "id": 104,
  "name": "Trending Sci-Fi Series",
  "description": "The highest rated sci-fi series and updates on our app.",
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
  "video_count": 12,
  "videos": {
    "total": 12,
    "page": 1,
    "limit": 20,
    "total_pages": 1,
    "items": [
      {
        "id": 101,
        "title": "Mad Max: Fury Road",
        "category": "action",
        "duration": "18:42",
        "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc123xyz/thumbnail.jpg",
        "views": 12400,
        "likes": 340,
        "is_liked": true,
        "is_saved": false,
        "watch_progress": {
          "last_position_seconds": 120,
          "completion_percentage": 10.5
        },
        "order": 1,
        "created_at": "2024-06-10T00:00:00Z"
      },
      {
        "id": 105,
        "title": "Blade Runner 2049 Analysis",
        "category": "sci-fi",
        "duration": "24:15",
        "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_xyz987/thumbnail.jpg",
        "views": 8900,
        "likes": 210,
        "is_liked": false,
        "is_saved": true,
        "watch_progress": null,
        "order": 2,
        "created_at": "2024-06-12T00:00:00Z"
      }
    ]
  }
}
```

#### Error Responses
- `404 Not Found`: Playlist primary key ID does not exist.
  ```json
  {
    "detail": "Playlist 999 not found"
  }
  ```

---

## 3. Data Integration Architecture

```
+--------------------------+          +--------------------------------------+
|   Mobile Client (App)    | -------> |  GET /api/v1/mobile/playlists       |
|  (iOS / Android Subscriber) |       |  (Public Playlists Catalog Feed)     |
+--------------------------+          +--------------------------------------+
             |
             | Taps Playlist Card (#104)
             v
+----------------------------------------------------------------------------+
|  GET /api/v1/mobile/playlists/104?page=1&limit=20                           |
|  -> Returns Header Metadata (Name, Banner, Video Count)                   |
|  -> Returns Ordered Video Items with Watch Progress & Subscriber Overlay   |
+----------------------------------------------------------------------------+
```
