# Creator Admin — Playlist Management API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints require a valid JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <creator_access_token>
```
### Standard HTTP Error Responses

All error responses across all endpoints follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid Request Payload
```json
{
  "detail": "Invalid video_ids array provided."
}
```

#### 2. `401 Unauthorized` — Missing or Expired JWT Token
```json
{
  "detail": "Could not validate credentials"
}
```

#### 3. `404 Not Found` — Resource Not Found or Forbidden Ownership
```json
{
  "detail": "Playlist 104 not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Database Error
```json
{
  "detail": "Internal server error while processing playlist request"
}
```

---

## 🎵 Admin Playlist Management Endpoints

### 1. `POST /api/v1/admin/playlists` — Create Playlist

Creates a new playlist container, links initial video IDs, and returns created playlist metadata.

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
  "video_count": 2,
  "created_at": "2024-06-20T10:30:00Z"
}
```

---

### 2. `GET /api/v1/admin/playlists` — List Creator Playlists (Paginated)

Retrieves a paginated list of lightweight playlist summaries belonging to the authenticated creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Request Query Parameters
- `search` (string, optional): Filter playlists by title/name substring.
- `sort` (string, optional, default: `"newest"`): Sorting order (`"newest"`, `"oldest"`, `"title"`, `"videoCount"`).
- `page` (integer, optional, default: `1`): Page number requested.
- `limit` (integer, optional, default: `20`, max: `100`): Number of items per page.

#### Example Request URL
```http
GET /api/v1/admin/playlists?page=1&limit=20
```

#### Response Specification (`200 OK`)
```json
{
  "total": 24,
  "page": 1,
  "limit": 20,
  "total_pages": 2,
  "items": [
    {
      "id": 104,
      "name": "Trending Sci-Fi Collection",
      "description": "The highest rated sci-fi series and updates on our app.",
      "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
      "video_count": 12,
      "created_at": "2024-05-01T00:00:00Z",
      "updated_at": "2024-06-10T00:00:00Z"
    }
  ]
}
```

---

### 3. `GET /api/v1/admin/playlists/{playlist_id}` — Get Playlist Details

Retrieves full metadata for a single playlist container.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Response Specification (`200 OK`)
```json
{
  "id": 104,
  "name": "Trending Sci-Fi Collection",
  "description": "The highest rated sci-fi series and updates on our app.",
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
  "video_count": 12,
  "created_at": "2024-05-01T00:00:00Z",
  "updated_at": "2024-06-10T00:00:00Z"
}
```

---

### 4. `PUT /api/v1/admin/playlists/{playlist_id}` — Update Playlist Details

Updates playlist textual metadata (`name`, `description`).

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
  "name": "Ultimate Sci-Fi & Action Vault",
  "description": "Updated master collection of action films."
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 104,
  "name": "Ultimate Sci-Fi & Action Vault",
  "description": "Updated master collection of action films.",
  "updated_at": "2024-06-20T10:30:00Z"
}
```

---

### 5. `POST /api/v1/admin/playlists/{playlist_id}/thumbnail/upload` — Upload Playlist Banner Image (Proxy Upload)

Uploads a playlist cover banner image (`assets/playlists/playlist_{id}.jpg`) securely through the backend proxy.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: multipart/form-data
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Request Body (`multipart/form-data`)
- `file` (binary image, required): Banner image file stream (`image/jpeg`, `image/png`, or `image/webp`).

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 6. `DELETE /api/v1/admin/playlists/{playlist_id}` — Delete Playlist

Deletes a playlist from the database and drops video link mappings (does NOT delete underlying videos).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

## 📽️ Playlist Video Attachment Sub-Resource Endpoints

### 7. `GET /api/v1/admin/playlists/{playlist_id}/videos` — List Videos Inside Playlist (Paginated)

Retrieves a paginated list of videos attached to a specific playlist with ordering and attached timestamp.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Request Query Parameters
- `search` (string, optional): Filter attached videos by title substring.
- `page` (integer, optional, default: `1`): Page number requested.
- `limit` (integer, optional, default: `20`, max: `100`): Number of attached video items per page.

#### Response Specification (`200 OK`)
```json
{
  "total": 12,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 101,
      "title": "Mad Max: Fury Road",
      "description": "A story set in a post-apocalyptic wasteland.",
      "category": "action",
      "status": "published",
      "is_playable": true,
      "views": 12400,
      "duration": "18:42",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc123xyz/thumbnail.jpg",
      "order": 1,
      "added_at": "2024-06-10T00:00:00Z"
    }
  ]
}
```

---

### 8. `POST /api/v1/admin/playlists/{playlist_id}/videos` — Add Videos to Playlist

Adds an array of video IDs to the specified playlist.

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
  "video_ids": [101, 102]
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 9. `DELETE /api/v1/admin/playlists/{playlist_id}/videos/{video_id}` — Remove Single Video from Playlist

Removes a single video from a playlist without deleting the video asset itself.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.
- `video_id` (integer, required): Database primary key ID of the video to remove.

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 10. `DELETE /api/v1/admin/playlists/{playlist_id}/videos` — Bulk Remove Videos from Playlist

Removes multiple videos from a playlist in a single batch request.

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
  "video_ids": [101, 102]
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 11. `GET /api/v1/admin/playlists/{playlist_id}/available_videos` — Get Available Videos for Playlist Picker (Paginated)

Fetches a paginated list of uploaded videos owned by the creator that are **not** currently included in the specified playlist (used for populating "Add Videos to Playlist" picker UI).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `playlist_id` (integer, required): Database primary key ID of the playlist.

#### Request Query Parameters
- `search` (string, optional): Search available videos by title substring.
- `category` (string, optional): Filter available videos by category ID/slug.
- `sort` (string, optional, default: `"newest"`): Sorting order (`"newest"`, `"oldest"`, `"views"`, `"title"`).
- `page` (integer, optional, default: `1`): Page number requested.
- `limit` (integer, optional, default: `20`, max: `100`): Number of items per page.

#### Example Request URL
```http
GET /api/v1/admin/playlists/104/available_videos?search=FastAPI&category=tutorials&sort=newest&page=1&limit=20
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
      "category": "sci-fi",
      "status": "published",
      "is_playable": true,
      "views": 18500,
      "duration": "148:00",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_abc888lmn/thumbnail.jpg",
      "created_at": "2024-05-20T00:00:00Z"
    }
  ]
}
```

---

### 12. `PUT /api/v1/admin/playlists/{playlist_id}/videos/reorder` — Reorder Videos inside Playlist

Persists updated sequence positions (`order`) of videos attached to a playlist following drag-and-drop actions in the Admin UI.

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
  "video_orders": [
    { "video_id": 105, "order": 1 },
    { "video_id": 101, "order": 2 }
  ]
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```
