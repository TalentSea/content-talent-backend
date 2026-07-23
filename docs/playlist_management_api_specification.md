# Playlist Management API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints require a valid JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <creator_access_token>
```
The creator identity (`user_id`) is extracted directly from the authenticated session context on the backend (`Depends(get_current_user)`). No `user_id` parameter is accepted in request bodies or query strings to eliminate **Insecure Direct Object Reference (IDOR)** risks.

### Architecture Overview
- **Backend Service**: FastAPI (Python) handles authentication, state persistence, authorization, and cloud handshakes.
- **Database**: Relational Database stores playlist metadata and video-playlist relation mappings.
- **Cloud Storage Service**: Bunny Storage API stores deterministic playlist cover banner assets (`assets/playlists/playlist_{id}.jpg`).

---

## 🎵 Playlist Management Endpoints

### 1. `POST /api/v1/playlists` — Create Playlist

Creates a new playlist for the creator and returns an explicit write-only upload path for the deterministic playlist cover banner image (`playlist_{id}.jpg`).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "name": "Trending Sci-Fi Collection",
  "description": "The highest rated sci-fi series and updates on our app.",
  "video_ids": [101, 105]
}
```

#### Response Specification (`201 Created`)
```json
{
  "id": 104,
  "name": "Trending Sci-Fi Collection",
  "description": "The highest rated sci-fi series and updates on our app.",
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
  "image_upload_url": "https://storage.bunnycdn.com/YOUR_ASSETS_BUCKET/assets/playlists/playlist_104.jpg",
  "video_count": 2,
  "videos": [
    {
      "id": 101,
      "title": "Mad Max: Fury Road",
      "description": "A story set in a post-apocalyptic wasteland.",
      "bunny_video_id": "vid_abc123xyz",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc123xyz/thumbnail.jpg"
    },
    {
      "id": 105,
      "title": "John Wick Masterclass",
      "description": "Action choreography breakdown.",
      "bunny_video_id": "vid_def456uvw",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_def456uvw/thumbnail.jpg"
    }
  ]
}
```

#### Client Execution Guide (Cover Banner Upload)
The frontend uploads the playlist cover image directly to Bunny Storage using the returned `image_upload_url`:
* **Purpose**: Streams raw banner image bytes directly to Bunny Storage bucket for cloud asset hosting.
* **Method**: `PUT`
* **Endpoint**: `https://storage.bunnycdn.com/YOUR_ASSETS_BUCKET/assets/playlists/playlist_104.jpg`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STORAGE_PASSWORD>
  Content-Type: image/jpeg
  ```
* **Request Body**: `[Raw Image Bytes]`
* **HTTP Status Codes**: `200 OK` / `201 Created`: `OK`

---

### 2. `GET /api/v1/playlists?page=1&limit=20` — List Creator Playlists (Paginated)

Retrieves a paginated list of playlists created by the authenticated creator formatted as lightweight summary objects for grid/list UI screens.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Request Query Parameters
- `page` (integer, optional, default: `1`): Page number requested.
- `limit` (integer, optional, default: `20`, max: `100`): Number of playlist items per page.

#### Example Request URL
```http
GET /api/v1/playlists?page=1&limit=20
```

#### Response Specification (`200 OK`)
```json
{
  "total": 12,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 104,
      "name": "Trending Sci-Fi Collection",
      "description": "The highest rated sci-fi series and updates on our app.",
      "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
      "video_count": 5
    },
    {
      "id": 108,
      "name": "Chill Documentaries",
      "description": "Nature docs to watch before bed.",
      "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_108.jpg",
      "video_count": 0
    }
  ]
}
```

---

### 3. `GET /api/v1/playlists/{playlist_id}?page=1&limit=20` — Get Playlist Details (Paginated Tracks)

Retrieves full details and a paginated list of associated video assets for a single playlist.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Request Query Parameters
- `page` (integer, optional, default: `1`): Page number for playlist videos.
- `limit` (integer, optional, default: `20`, max: `100`): Video items per page.

#### Example Request URL
```http
GET /api/v1/playlists/104?page=1&limit=20
```

#### Response Specification (`200 OK`)
```json
{
  "id": 104,
  "name": "Trending Sci-Fi Collection",
  "description": "The highest rated sci-fi series and updates on our app.",
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
  "video_count": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3,
  "videos": [
    {
      "id": 101,
      "title": "Mad Max: Fury Road",
      "description": "A story set in a post-apocalyptic wasteland.",
      "bunny_video_id": "vid_abc123xyz",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc123xyz/thumbnail.jpg"
    },
    {
      "id": 105,
      "title": "John Wick Masterclass",
      "description": "Action choreography breakdown.",
      "bunny_video_id": "vid_def456uvw",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_def456uvw/thumbnail.jpg"
    }
  ]
}
```

---

### 4. `PUT /api/v1/playlists/{playlist_id}` — Edit Playlist Details

Updates playlist textual metadata (`name`, `description`) or associated video IDs list.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Request Body
```json
{
  "name": "My Updated Sci-Fi & Action Favorites",
  "description": "An edited collection of action and sci-fi blockbusters.",
  "video_ids": [101, 102]
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 104,
  "name": "My Updated Sci-Fi & Action Favorites",
  "description": "An edited collection of action and sci-fi blockbusters.",
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
  "video_count": 2,
  "videos": [
    {
      "id": 101,
      "title": "Mad Max: Fury Road",
      "description": "A story set in a post-apocalyptic wasteland.",
      "bunny_video_id": "vid_abc123xyz",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc123xyz/thumbnail.jpg"
    },
    {
      "id": 102,
      "title": "Inception",
      "description": "A thief who steals corporate secrets through dream-sharing technology.",
      "bunny_video_id": "vid_abc888lmn",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc888lmn/thumbnail.jpg"
    }
  ]
}
```

---

### 5. `POST /api/v1/playlists/{playlist_id}/thumbnail/upload-url` — Request Playlist Banner Upload URL

Generates a write-only presigned cloud upload URL to override or update the playlist's deterministic cover banner image (`playlist_{id}.jpg`).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Response Specification (`200 OK`)
```json
{
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
  "image_upload_url": "https://storage.bunnycdn.com/YOUR_ASSETS_BUCKET/assets/playlists/playlist_104.jpg"
}
```

#### Client Execution Guide (Cover Banner Override Upload)
The frontend streams raw image bytes to `image_upload_url` via HTTP `PUT` to overwrite the existing playlist cover banner directly on Bunny Storage:
* **Method**: `PUT`
* **Endpoint**: `https://storage.bunnycdn.com/YOUR_ASSETS_BUCKET/assets/playlists/playlist_104.jpg`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STORAGE_PASSWORD>
  Content-Type: image/jpeg
  ```
* **Request Body**: `[Raw Image Bytes]`
* **HTTP Status Codes**: `200 OK` / `201 Created`: `OK`

---

### 6. `DELETE /api/v1/playlists/{playlist_id}` — Delete Playlist

Deletes a playlist owned by the creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Response Specification (`200 OK`)
```json
{
  "status": "success",
  "message": "Successfully deleted"
}
```

---

### 7. `GET /api/v1/playlists/{playlist_id}/available_videos?page=1&limit=20` — Get Available Videos for Playlist (Paginated)

Fetches a paginated list of uploaded videos owned by the creator that are **not** currently included in the specified playlist (used for populating "Add Videos to Playlist" picker UI).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Request Query Parameters
- `page` (integer, optional, default: `1`): Page number requested.
- `limit` (integer, optional, default: `20`, max: `100`): Number of items per page.

#### Example Request URL
```http
GET /api/v1/playlists/104/available_videos?page=1&limit=20
```

#### Response Specification (`200 OK`)
```json
{
  "total": 60,
  "page": 1,
  "limit": 20,
  "total_pages": 3,
  "items": [
    {
      "id": 102,
      "title": "Inception",
      "description": "A thief who steals corporate secrets through dream-sharing technology.",
      "bunny_video_id": "vid_abc888lmn",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc888lmn/thumbnail.jpg"
    },
    {
      "id": 103,
      "title": "Interstellar",
      "description": "A team of explorers travel through a wormhole in space.",
      "bunny_video_id": "vid_dfg444opq",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_dfg444opq/thumbnail.jpg"
    }
  ]
}
```
