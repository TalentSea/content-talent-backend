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
- **Cloud Video Service**: Bunny Stream API handles video containers, encoding, and HLS streaming.
- **Cloud Storage Service**: Bunny Storage API stores and serves all primary (Slot 0) and alternative (Slots 1 & 2) thumbnails via public Storage Pull Zone.
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

#### 🔄 Frontend Client Integration Sequences (Form Submission Workflows)

When building the creator upload form/modal in React/React Native, the frontend calls APIs in these exact step-by-step sequences:

##### Sequence A: Save as Draft Flow
1. Call `POST /api/v1/admin/videos/initiate` with `"status": "draft"` ➔ Receive `id` (e.g. `101`).
2. *(Optional)* Call `POST /api/v1/admin/videos/101/thumbnails/upload?slot=0` with cover image binary.
3. Stream video file chunks directly to Bunny TUS `https://video.bunnycdn.com/tusupload`.

##### Sequence B: Publish Immediately Flow
1. Call `POST /api/v1/admin/videos/initiate` ➔ Receive `id` (e.g. `101`).
2. Immediately Call `POST /api/v1/admin/videos/101/publish` ➔ Video status becomes `"published"`.
3. *(Optional)* Call `POST /api/v1/admin/videos/101/thumbnails/upload?slot=0` with cover image binary.
4. Stream video file chunks directly to Bunny TUS `https://video.bunnycdn.com/tusupload`.

##### Sequence C: Schedule Publication Flow
1. Call `POST /api/v1/admin/videos/initiate` ➔ Receive `id` (e.g. `101`).
2. Immediately Call `POST /api/v1/admin/videos/101/schedule` with `{ "date": "YYYY-MM-DD", "time": "HH:MM" }` ➔ Video status becomes `"scheduled"`.
3. *(Optional)* Call `POST /api/v1/admin/videos/101/thumbnails/upload?slot=0` with cover image binary.
4. Stream video file chunks directly to Bunny TUS `https://video.bunnycdn.com/tusupload`.

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

#### Internal Backend & State Machine Workflows

##### Sub-Step A: Status Resolution Mapping
* **Purpose**: Maps Bunny Stream integer status code (0–10) to internal system state (`PENDING`, `ENCODING`, `READY`, `PLAYABLE`, `FAILED`).

##### Sub-Step B: State Machine Persistence
* **Purpose**: Updates `status`, `encode_progress`, and `is_playable` flags on the `videos` record in SQLite using `VideoGuid` as the lookup key.

##### Sub-Step C: Auto-Population of Duration & Release Date
* **Purpose**: When status reaches `READY`/`PLAYABLE` (100% encoded), queries Bunny Stream API for raw video `length` in seconds, converts `length` into duration string (`"02:22"`), and sets `published_at = datetime.utcnow()` if not already populated.

##### Sub-Step D: Automated HLS Caption Manifest Embedding
* **Purpose**: When status code `9` (`CaptionsGenerated`) arrives, fetches the generated `.vtt` content via Bunny Stream REST API (`GET https://video.bunnycdn.com/library/{id}/videos/{guid}/captions/en` using `BUNNY_STREAM_API_KEY`), base64 encodes it, and posts it to `POST https://video.bunnycdn.com/library/{id}/videos/{guid}/captions/en`.
* **Result**: Bunny Stream bakes `#EXT-X-MEDIA:TYPE=SUBTITLES` directly into `playlist.m3u8`, enabling native CC buttons on mobile players out of the box!

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

#### Internal Backend & Query Execution Workflows

##### Sub-Step A: Auto-Publishing Trigger
* **Purpose**: Before fetching video items, executes database check `publish_due_scheduled_videos()` to immediately release any scheduled videos whose target date/time has arrived.

##### Sub-Step B: SQL Filter & Pagination Assembly
* **Purpose**: Constructs Peewee query filtered by `Video.user == user_id`, applying search substrings, category IDs, date bounds, and `paginate(page, limit)`.

##### Sub-Step C: Duration & Metadata Auto-Sync
* **Purpose**: Inspects retrieved video records. If any playable video is missing `duration` or `published_at`, auto-fetches `length` from Bunny Stream API and persists duration to SQLite.

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
      "captions_data": [
        {
          "srclang": "en-auto",
          "label": "EN",
          "is_default": true,
          "url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/captions/en-auto.vtt"
        }
      ],
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

#### Internal Backend Workflows

##### Sub-Step A: Ownership Verification & Live Cloud Sync
* **Purpose**: Verifies `Video.user == user_id`. If `status` is `ENCODING` or `PROCESSING`, calls Bunny Stream API (`GET /library/{id}/videos/{guid}`) to query live `encodeProgress` and sync database.

##### Sub-Step B: Tokenized Presigned HLS URL Generation
* **Purpose**: If video `is_playable == true`, computes time-bound HMAC tokenized streaming URL (`playlist.m3u8?token=...&expires=...`) for authorized preview playback.

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
  "main_thumbnail_url": "https://your-storage-pull-zone.b-cdn.net/vid_987654321_abc/thumb_1.jpg",
  "alt_thumbnail_urls": [
    "https://your-storage-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-storage-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ],
  "captions_data": [],
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
  "main_thumbnail_url": "https://your-storage-pull-zone.b-cdn.net/vid_987654321_abc/thumb_1.jpg",
  "alt_thumbnail_urls": [
    "https://your-storage-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-storage-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ],
  "captions_data": [
    {
      "srclang": "en-auto",
      "label": "EN",
      "is_default": true,
      "url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/captions/en-auto.vtt"
    }
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

Uploads a thumbnail image binary (`slot: 0` for main cover `thumb_1.{ext}`, `slot: 1` for `thumb_2.{ext}`, `slot: 2` for `thumb_3.{ext}`) securely to Bunny Storage Zone through the backend proxy. Dynamically detects image extension (`.png`, `.jpg`, `.webp`) and updates the database record.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: multipart/form-data
```

#### Query Parameters
- `slot` (integer, required, default: `0`): Target slot (`0` for Main Cover, `1` for Alt 1, `2` for Alt 2).

#### Request Body (`multipart/form-data`)
- `file` (binary image, required): Image file stream (`image/jpeg`, `image/png`, or `image/webp`).

#### Internal Backend Workflows

##### Sub-Step A: Target Slot Resolution
* **Purpose**: Inspects `slot` query parameter (`0` = main cover `thumb_1.{ext}`, `1` = `thumb_2.{ext}`, `2` = `thumb_3.{ext}`).

##### Sub-Step B: Bunny Storage Zone Upload Proxy
* **Purpose**: Streams binary image to Bunny Storage Zone path `{bunny_video_id}/thumb_{slot+1}.{ext}` via HTTP `PUT` request without exposing cloud API keys to frontend.

##### Sub-Step C: Database Record Update
* **Purpose**: If `slot == 0`, updates `main_thumbnail_url`. If `slot == 1` or `2`, updates alternative thumbnail URL array.

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

#### Internal Backend Workflows

##### Sub-Step A: Cover Swap Operation
* **Purpose**: Replaces `main_thumbnail_url` with `selected_main_thumbnail` URL and moves old main URL into `alt_thumbnail_urls` array in SQLite.

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 8. `DELETE /api/v1/admin/videos/{video_id}/thumbnails` — Delete Alternative Thumbnail

Deletes a backup alternative thumbnail asset permanently from Bunny Storage and removes its URL entry from the database.

#### Internal Backend Workflows

##### Sub-Step A: Bunny Storage Cloud File Deletion
* **Purpose**: Extracts filename from target URL and sends HTTP `DELETE` to Bunny Storage API path `{bunny_video_id}/{filename}`.

##### Sub-Step B: Database List Removal
* **Purpose**: Removes deleted image URL from `alt_thumbnail_urls` array in SQLite.

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 9. `DELETE /api/v1/admin/videos/{video_id}` — Delete Video Asset

Deletes a video asset from the backend database and deletes the underlying container on Bunny Stream.

#### Internal Backend Workflows

##### Sub-Step A: Cloud Asset Purge
* **Purpose**: Issues HTTP `DELETE` to Bunny Stream API (`DELETE /library/{id}/videos/{guid}`) and purges all thumbnail images from Bunny Storage Zone.

##### Sub-Step B: Database Record Drop
* **Purpose**: Removes the video row permanently from SQLite `videos` table.

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

#### Internal Backend Workflows

##### Sub-Step A: Immediate Release Transition
* **Purpose**: Updates `status = "published"`, records `published_at = datetime.utcnow()`, and clears `scheduled_at = NULL` in SQLite. Video is instantly made live for subscribers!

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

Schedules a video asset for automated future publication at a specific target date and time.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "date": "2026-08-01",
  "time": "18:00"
}
```

#### Internal Backend & Automated Publishing Workflows

##### Sub-Step A: Request Validation & Datetime Parsing
* **Purpose**: Validates JWT authorization ownership and parses `date` (`YYYY-MM-DD`) and `time` (`HH:MM`) strings into a native Python `datetime` object (`YYYY-MM-DD HH:MM:00`).

##### Sub-Step B: Database State Persistence
* **Purpose**: Commits the state change in SQLite (`status = "scheduled"`, `scheduled_at = datetime`). The video remains hidden from the subscriber catalog app until `scheduled_at` time arrives.

##### Sub-Step C: Automated 60-Second Background Publisher
* **Purpose**: A background loop in `app/main.py` runs every 60 seconds executing a bulk SQL update:
  `UPDATE videos SET status = 'published', published_at = scheduled_at, scheduled_at = NULL WHERE status = 'scheduled' AND scheduled_at <= datetime('now')`
* **Result**: Once local time reaches `scheduled_at`, the video status automatically flips to `"published"` and becomes live for all subscribers!

#### Response Specification (`200 OK`)
```json
{
  "id": 101,
  "status": "scheduled",
  "scheduled_at": "2026-08-01T18:00:00"
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

#### Internal Backend Workflows

##### Sub-Step A: Ownership Authorization & DB Fetch
* **Purpose**: Fetches video records matching `video_ids` array where `Video.user == user_id`.

##### Sub-Step B: Batch Cloud Asset Purge
* **Purpose**: Iterates over matching videos, deleting Bunny Stream containers (`DELETE /library/{id}/videos/{guid}`) and removing thumbnail files from Bunny Storage.

##### Sub-Step C: Bulk SQL Record Deletion
* **Purpose**: Deletes matching rows from SQLite `videos` table in a single batch query (`DELETE FROM video WHERE id IN (...) AND user_id = ...`).

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```
