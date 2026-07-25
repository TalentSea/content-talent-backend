# Creator Admin — Video Management API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints (excluding third-party webhooks) require a valid JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <creator_access_token>
```
The creator identity (`user_id`) is extracted directly from the authenticated session context on the backend (`Depends(get_current_user)`). No `user_id` parameter is accepted in request bodies or query strings to eliminate **Insecure Direct Object Reference (IDOR)** risks.

### Architecture Overview
- **Backend Service**: FastAPI (Python) handles authentication, state persistence, authorization, and cloud handshakes.
- **Database**: Relational Database stores video metadata and cloud asset mappings.
- **Cloud Video Service**: Bunny Stream API handles video containers, transcoding, HLS streaming, and thumbnail hosting.
- **Cloud Storage Service**: Bunny Storage API stores alternative backup thumbnails.
### Standard HTTP Error Responses

All error responses across all endpoints follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid Request Payload
```json
{
  "detail": "Invalid thumbnail slot. Slot must be 0, 1, or 2."
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
  "detail": "Video asset 101 not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Cloud Service or Database Error
```json
{
  "detail": "Failed to communicate with Bunny Stream API"
}
```

---

## 📹 Admin Video Management Endpoints

### 1. `POST /api/v1/admin/videos/initiate` — Initiate Video Upload

Initiates a video upload session by creating a video container on Bunny Stream, generating a SHA-256 presigned authorization signature, and saving an initial `PENDING` record in the database.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "title": "Introduction to FastAPI & OTT Streaming",
  "description": "Learn how to build a production grade video upload pipeline using Bunny.net.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"],
  "status": "draft"
}
```

* `status` (string, optional, default: `"draft"`): Initial video state (`"draft"` or `"published"`).

#### Internal Backend & External Cloud Workflows

##### Sub-Step A: Backend -> Bunny Stream API (Create Video Container Slot)
* **Purpose**: Reserves an empty video slot on Bunny Stream to generate a unique `guid` (`bunny_video_id`). This GUID is required for HMAC signature calculation, client-side TUS streaming, and CDN URL construction.
* **Method**: `POST`
* **Endpoint**: `https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}/videos`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STREAM_API_KEY>
  Accept: application/json
  Content-Type: application/json
  ```
* **Request Body**:
  ```json
  {
    "title": "Introduction to FastAPI & OTT Streaming"
  }
  ```
* **Response Body (`200 OK`)**:
  ```json
  {
    "videoLibraryId": 123456,
    "guid": "vid_987654321_abc",
    "title": "Introduction to FastAPI & OTT Streaming",
    "dateCreated": "2026-07-22T07:15:00.000Z",
    "views": 0,
    "hasMP4Fallback": false,
    "availableResolutions": null,
    "thumbnailCount": 0,
    "encodeProgress": 0,
    "storageSize": 0,
    "captions": [],
    "status": 0
  }
  ```

##### Sub-Step B: Backend HMAC Presigned Signature Generation
* **Purpose**: Computes a time-bound SHA-256 presigned token (`signature` & `expiration_time`) allowing the client application to stream video chunks directly to Bunny TUS without exposing the master `BUNNY_STREAM_API_KEY`.
* **Formula**: `signature = SHA256(library_id + bunny_api_key + expiration_time + bunny_video_id)`

##### Sub-Step C: Database Record Insertion
* **Purpose**: Commits the video record (`status = PENDING`) linked to the creator's `user_id` in the database.

#### Response Specification (`201 Created`)
```json
{
  "id": 101,
  "bunny_video_id": "vid_987654321_abc",
  "bunny_library_id": "123456",
  "status": "PENDING",
  "signature": "a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
  "expiration_time": 1719818600
}
```

#### Client Execution Guide (Post-Initiation Uploads)

##### 1. Cover & Backup Thumbnail Upload (Client -> FastAPI Backend Proxy)
* **Purpose**: Uploads primary cover image (`slot=0`) or alternative backup images (`slot=1`, `slot=2`) securely through FastAPI backend without exposing master cloud API keys or passwords.
* **Method**: `POST`
* **Endpoint**: `/api/v1/admin/videos/{video_id}/thumbnails/upload?slot=0`
* **Headers**:
  ```http
  Authorization: Bearer <creator_access_token>
  Content-Type: multipart/form-data
  ```
* **Request Body**: `[FormData with "file" image binary]`

##### 2. Resumable Video File Streaming (Client -> Bunny TUS Protocol)
* **Purpose**: Streams raw video bytes directly to Bunny's TUS server using returned presigned credentials, enabling auto-resumption and chunk retries.
* **Method**: `POST` & `PATCH`
* **Endpoint**: `https://video.bunnycdn.com/tusupload`
* **Request Headers**:
  ```http
  AuthorizationSignature: <signature>
  AuthorizationExpire: <expiration_time>
  VideoId: <bunny_video_id>
  LibraryId: <bunny_library_id>
  ```

---

### 2. `POST /api/v1/webhooks/bunny` — Transcoding Webhook Handler

Called automatically by Bunny Stream background servers whenever a video changes encoding state.

#### Request Headers
```http
Content-Type: application/json
User-Agent: BunnyCDN-Webhook
```

#### Request Body (Bunny Stream -> Backend)
```json
{
  "VideoLibraryId": 123456,
  "VideoGuid": "vid_987654321_abc",
  "Status": 3
}
```

#### Official Bunny Stream Status Code State Machine

| Status Code | Status Name | Description | Backend Action |
| :---: | :--- | :--- | :--- |
| `0` | **Queued** | Video queued for encoding. | Status = `PENDING` |
| `1` | **Processing** | Video processing preview & metadata. | Status = `PROCESSING` |
| `2` | **Encoding** | Video currently encoding formats. | Status = `ENCODING` |
| `3` | **Finished** | Video encoding finished across all resolutions. | Status = `READY` (`encode_progress` = 100) |
| `4` | **Resolution Finished** | First resolution ready. Video is playable! | Status = `PLAYABLE` (`is_playable` = true) |
| `5` | **Failed** | Video encoding failed. | Status = `FAILED` |
| `6` | **PresignedUploadStarted** | Upload session initiated. | Log event |
| `7` | **PresignedUploadFinished** | Upload bytes received by Bunny. | Status = `UPLOAD_FINISHED` |
| `8` | **PresignedUploadFailed** | Upload failed or interrupted. | Status = `UPLOAD_FAILED` |
| `9` | **CaptionsGenerated** | Automatic captions generated. | Store captions metadata |
| `10` | **TitleOrDescriptionGenerated** | AI title/description generated. | Update metadata |

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 3. `GET /api/v1/admin/videos` — List Creator Videos (Paginated & Filterable)

Retrieves a paginated list of uploaded videos belonging to the authenticated creator with optional filtering, title search, and sorting.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Request Query Parameters
- `status` (string, optional): Filter by publication state (`"published"`, `"draft"`, `"scheduled"`).
- `category` (string, optional): Category ID or slug string.
- `search` (string, optional): Search query to filter videos by title substring.
- `sort` (string, optional, default: `"newest"`): Sorting order (`"newest"`, `"oldest"`, `"views"`, `"title"`).
- `dateFrom` (string, optional): ISO date string filtering creation start (e.g. `"2024-01-01"`).
- `dateTo` (string, optional): ISO date string filtering creation end (e.g. `"2024-06-30"`).
- `page` (integer, optional, default: `1`): Page number requested.
- `limit` (integer, optional, default: `20`, max: `100`): Number of video items per page.

#### Example Request URL
```http
GET /api/v1/admin/videos?status=published&search=FastAPI&sort=newest&page=1&limit=20
```

#### Response Specification (`200 OK`)
```json
{
  "total": 105,
  "page": 1,
  "limit": 20,
  "total_pages": 6,
  "items": [
    {
      "id": 101,
      "title": "Introduction to FastAPI & OTT Streaming",
      "description": "Learn how to build a production grade video upload pipeline using Bunny.net.",
      "category": "tutorials",
      "tags": ["fastapi", "python", "bunny-stream"],
      "status": "published",
      "encode_progress": 100,
      "is_playable": true,
      "views": 12400,
      "duration": "18:42",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
      "published_at": "2024-06-01T00:00:00Z",
      "scheduled_at": null,
      "created_at": "2024-05-20T00:00:00Z"
    }
  ]
}
```

---

### 4. `GET /api/v1/admin/videos/{video_id}` — Get Video Details & Transcoding Progress

Retrieves detailed metadata for a single video. If the video is currently `ENCODING`, the backend queries Bunny Stream to sync the latest `encodeProgress`.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Response Specification (`200 OK`)

##### Scenario A: During Transcoding (`status: "ENCODING"`)
```json
{
  "id": 101,
  "title": "Introduction to FastAPI & OTT Streaming",
  "description": "Learn how to build a production grade video upload pipeline using Bunny.net.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"],
  "status": "ENCODING",
  "encode_progress": 65,
  "is_playable": false,
  "views": 0,
  "duration": null,
  "playback_url": null,
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ],
  "published_at": null,
  "scheduled_at": null,
  "created_at": "2024-05-20T00:00:00Z"
}
```

##### Scenario B: Transcoding Finished & Ready (`status: "published"`)
```json
{
  "id": 101,
  "title": "Introduction to FastAPI & OTT Streaming",
  "description": "Learn how to build a production grade video upload pipeline using Bunny.net.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"],
  "status": "published",
  "encode_progress": 100,
  "is_playable": true,
  "views": 12400,
  "duration": "18:42",
  "playback_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/playlist.m3u8?token=a1b2c3d4e5f6...&expires=1719825600",
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ],
  "published_at": "2024-06-01T00:00:00Z",
  "scheduled_at": null,
  "created_at": "2024-05-20T00:00:00Z"
}
```

---

### 5. `PATCH /api/v1/admin/videos/{video_id}` — Edit Video Textual Metadata

Updates textual metadata fields (`title`, `description`, `category`, `tags`) for a specific video asset owned by the creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Request Body Schema (Partial Updates - All Fields Optional)
* `title` (string, optional): Updated video title.
* `description` (string, optional): Updated video description.
* `category` (string, optional): Updated category ID or slug.
* `tags` (array of strings, optional): Updated tag keywords.

##### Example Request Body
```json
{
  "title": "Introduction to FastAPI & OTT Streaming (Updated HD)",
  "description": "Updated masterclass description.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"]
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 101,
  "title": "Introduction to FastAPI & OTT Streaming (Updated HD)",
  "description": "Updated masterclass description.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"],
  "status": "published"
}
```

---

### 6. `POST /api/v1/admin/videos/{video_id}/thumbnails/upload` — Upload Thumbnail Image (Proxy Upload)

Uploads a thumbnail image binary (`slot: 0` for main cover, `slot: 1` or `2` for alternative backup thumbnails) securely through the backend proxy.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: multipart/form-data
```

#### Query Parameters
- `slot` (integer, required, default: `0`): Target slot (`0` for Main Cover, `1` for Alt 1, `2` for Alt 2).

#### Request Body (`multipart/form-data`)
- `file` (binary image, required): Image file stream (`image/jpeg`, `image/png`, or `image/webp`).

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 7. `PATCH /api/v1/admin/videos/{video_id}/thumbnails/select-main` — Select Main Cover Thumbnail

Promotes an existing alternative thumbnail to be the primary cover image and swaps the previous main cover into the alternative thumbnail list.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Request Body Schema
* `selected_main_thumbnail` (string, required): Full CDN URL of the alternative thumbnail to promote as the primary cover image.

##### Example Request Body
```json
{
  "selected_main_thumbnail": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg"
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 8. `DELETE /api/v1/admin/videos/{video_id}/thumbnails` — Delete Alternative Thumbnail

Deletes a backup alternative thumbnail asset permanently from Bunny Storage and removes its URL entry from the database.

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 9. `DELETE /api/v1/admin/videos/{video_id}` — Delete Video Asset

Deletes a video asset from the backend database and deletes the underlying container on Bunny Stream.

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 10. `POST /api/v1/admin/videos/{video_id}/publish` — Publish Video Immediately

Publishes a video asset immediately, updating its state to `published` and recording the ISO UTC timestamp in `published_at`.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Response Specification (`200 OK`)
```json
{
  "id": 101,
  "status": "published",
  "published_at": "2024-06-20T10:30:00Z"
}
```

---

### 11. `POST /api/v1/admin/videos/{video_id}/schedule` — Schedule Video Publishing

Schedules a video asset for automated future publication at a specific date, time, and timezone.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "date": "2024-07-01",
  "time": "09:00",
  "timezone": "America/Los_Angeles"
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 101,
  "status": "scheduled",
  "scheduled_at": "2024-07-01T16:00:00Z"
}
```

---

### 12. `POST /api/v1/admin/videos/bulk-delete` — Bulk Delete Video Assets

Deletes multiple video assets from the backend database and drops their containers on Bunny Stream in a single batch call (used for Admin Table multi-select deletion).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "video_ids": [101, 102, 105]
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```
