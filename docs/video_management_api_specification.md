# Video Management API Specification

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
- **Stream Security**: Playback URLs use time-bound presigned tokens (`playlist.m3u8?token=...&expires=...`) to prevent hotlinking and URL piracy.

---

## 📹 Video Management Endpoints

### 1. `POST /api/v1/videos/initiate` — Initiate Video Upload

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
  "thumbnails": [
    { "slot": 0, "filename": "hero_cover.jpg" },
    { "slot": 1, "filename": "thumbnail_2.jpg" },
    { "slot": 2, "filename": "thumbnail_3.jpg" }
  ]
}
```

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
  "expiration_time": 1719818600,
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ]
}
```

#### Client Execution Guide (Post-Initiation Uploads)

##### 1. Main Thumbnail Upload (Client -> Bunny Stream)
* **Purpose**: Uploads the primary cover image directly to Bunny Stream, which saves it automatically as `thumbnail.jpg`.
* **Method**: `PUT`
* **Endpoint**: `https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}/videos/{bunny_video_id}/thumbnail`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STREAM_API_KEY>
  Content-Type: image/jpeg
  ```
* **Request Body**: `[Raw Image Bytes]`
* **HTTP Status Codes**:
  - `200 OK`: `OK`
  - `401 Unauthorized`: Invalid or missing `AccessKey`.
  - `404 Not Found`: Invalid `BUNNY_LIBRARY_ID` or `bunny_video_id`.
  - `400 Bad Request`: Corrupt image file stream or invalid image content-type.

##### 2. Alternative Thumbnail Upload (Client -> Bunny Storage)
* **Purpose**: Uploads secondary/backup cover images (`thumb_2.jpg`, `thumb_3.jpg`) directly to Bunny Storage.
* **Method**: `PUT`
* **Endpoint**: `https://storage.bunnycdn.com/{BUNNY_STORAGE_ZONE_NAME}/{bunny_video_id}/thumb_2.jpg`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STORAGE_PASSWORD>
  Content-Type: image/jpeg
  ```
* **Request Body**: `[Raw Image Bytes]`
* **HTTP Status Codes**:
  - `200 OK` / `201 Created`: `OK`
  - `401 Unauthorized`: Invalid `AccessKey` (Storage Password).
  - `404 Not Found`: Invalid Storage Zone name or path.

##### 3. Resumable Video File Streaming (Client -> Bunny TUS Protocol)
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
* **HTTP Status Codes**:
  - `201 Created`: TUS upload session established (`POST`).
  - `204 No Content`: Chunk uploaded successfully (`PATCH`).
  - `401 Unauthorized`: Expired or invalid presigned signature.
  - `404 Not Found`: Video ID or Library ID not found.
  - `413 Payload Too Large`: File exceeds storage limit.
* **Client Code (`tus-js-client`)**:
  ```javascript
  import * as tus from "tus-js-client";

  const { bunny_video_id, bunny_library_id, expiration_time, signature } = initiateData;
  const file = document.getElementById("fileInput").files[0];

  const upload = new tus.Upload(file, {
    endpoint: "https://video.bunnycdn.com/tusupload",
    retryDelays: [0, 3000, 5000, 10000, 20000, 60000, 60000],
    headers: {
      AuthorizationSignature: signature,
      AuthorizationExpire: expiration_time,
      VideoId: bunny_video_id,
      LibraryId: bunny_library_id,
    },
    metadata: { filetype: file.type, title: file.name },
    onProgress: function (bytesUploaded, bytesTotal) {
      console.log(`Progress: ${((bytesUploaded / bytesTotal) * 100).toFixed(2)}%`);
    },
    onSuccess: function () { console.log("Upload complete!"); }
  });

  upload.findPreviousUploads().then(function (previousUploads) {
    if (previousUploads.length) upload.resumeFromPreviousUpload(previousUploads[0]);
    upload.start();
  });
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

#### Official Bunny Status Code State Machine

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

### 3. `GET /api/v1/videos?page=1&limit=20` — List Creator Videos (Paginated)

Retrieves a paginated list of uploaded videos belonging to the authenticated creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Request Query Parameters
- `page` (integer, optional, default: `1`): Page number requested.
- `limit` (integer, optional, default: `20`, max: `100`): Number of video items per page.

#### Example Request URL
```http
GET /api/v1/videos?page=1&limit=20
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
      "bunny_video_id": "vid_987654321_abc",
      "status": "ENCODING",
      "encode_progress": 65,
      "is_playable": false,
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg"
    },
    {
      "id": 105,
      "title": "John Wick Masterclass",
      "description": "Action choreography breakdown.",
      "category": "entertainment",
      "tags": ["action", "movies"],
      "bunny_video_id": "vid_def456uvw",
      "status": "READY",
      "encode_progress": 100,
      "is_playable": true,
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_def456uvw/thumbnail.jpg"
    }
  ]
}
```

---

### 4. `GET /api/v1/videos/{video_id}` — Get Video Details & Transcoding Progress

Retrieves detailed metadata for a single video. If the video is currently `ENCODING`, the backend queries Bunny Stream to sync the latest `encodeProgress`.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Internal Backend & External Cloud Workflows

##### Sub-Step A: Backend -> Bunny Stream API (Live Status Sync)
* **Purpose**: Fetches real-time `encodeProgress` (0% to 100%) directly from Bunny Stream when the video is in `ENCODING` state to update database cache and provide accurate progress indicators in the UI.
* **Method**: `GET`
* **Endpoint**: `https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}/videos/{bunny_video_id}`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STREAM_API_KEY>
  Accept: application/json
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
    "availableResolutions": "240p,360p,720p",
    "thumbnailCount": 1,
    "encodeProgress": 65,
    "storageSize": 157286400,
    "captions": [],
    "status": 2
  }
  ```

#### Response Specification (`200 OK`)

##### Scenario A: During Transcoding (`status: "ENCODING"`)
```json
{
  "id": 101,
  "bunny_video_id": "vid_987654321_abc",
  "title": "Introduction to FastAPI & OTT Streaming",
  "description": "Learn how to build a production grade video upload pipeline using Bunny.net.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"],
  "status": "ENCODING",
  "encode_progress": 65,
  "is_playable": false,
  "playback_url": null,
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ],
  "created_at": "2026-07-22T07:15:00Z"
}
```

##### Scenario B: Transcoding Finished & Ready for Playback (`status: "READY"`)
```json
{
  "id": 101,
  "bunny_video_id": "vid_987654321_abc",
  "title": "Introduction to FastAPI & OTT Streaming",
  "description": "Learn how to build a production grade video upload pipeline using Bunny.net.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"],
  "status": "READY",
  "encode_progress": 100,
  "is_playable": true,
  "playback_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/playlist.m3u8?token=a1b2c3d4e5f6...&expires=1719825600",
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ],
  "created_at": "2026-07-22T07:15:00Z"
}
```

---

### 5. `PATCH /api/v1/videos/{video_id}` — Edit Video Textual Metadata

Updates textual metadata fields (`title`, `description`, `category`, `tags`) for a specific video asset owned by the creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Request Body
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
  "bunny_video_id": "vid_987654321_abc",
  "title": "Introduction to FastAPI & OTT Streaming (Updated HD)",
  "description": "Updated masterclass description.",
  "category": "tutorials",
  "tags": ["fastapi", "python", "bunny-stream"],
  "status": "READY",
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ]
}
```

---

### 6. `POST /api/v1/videos/{video_id}/thumbnails/upload-url` — Request Thumbnail Upload URL

Generates a write-only presigned cloud upload URL for a specific 0-indexed thumbnail slot (`slot: 0` for main cover, `slot: 1` or `2` for alternative backup thumbnails).

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Request Body Schema
* `slot` (integer, required): `0` for Main Cover, `1` for Alt Thumbnail 1, `2` for Alt Thumbnail 2.
* `filename` (string, required): Original filename selected on client device.

##### Example Request Body (`slot: 0` — Main Cover)
```json
{
  "slot": 0,
  "filename": "hero_cover_v2.jpg"
}
```

##### Example Request Body (`slot: 1` — Alt Thumbnail 1)
```json
{
  "slot": 1,
  "filename": "backup_banner_1.jpg"
}
```

#### Response Specification (`200 OK`)

##### For `slot: 0` (Main Cover Upload)
```json
{
  "slot": 0,
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "image_upload_url": "https://video.bunnycdn.com/library/123456/videos/vid_987654321_abc/thumbnail"
}
```

##### For `slot: 1` (Alt Thumbnail 1 Upload)
```json
{
  "slot": 1,
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
  "image_upload_url": "https://storage.bunnycdn.com/YOUR_STORAGE_ZONE/vid_987654321_abc/thumb_2.jpg"
}
```

#### Client Execution Guide (Direct Cloud Image Upload)
* **Purpose**: Streams raw image bytes directly to Bunny Stream API (`slot: 0`) or Bunny Storage Bucket (`slot: 1` / `slot: 2`).
* **Method**: `PUT`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STREAM_API_KEY> (for slot: 0) OR <BUNNY_STORAGE_PASSWORD> (for slot: 1, 2)
  Content-Type: image/jpeg
  ```
* **Request Body**: `[Raw Image Bytes]`
* **HTTP Status Codes**: `200 OK` / `201 Created`: `OK`

---

### 7. `PATCH /api/v1/videos/{video_id}/thumbnails/select-main` — Select Main Cover Thumbnail

Promotes an existing alternative thumbnail to be the primary cover image and swaps the previous main cover into the alternative thumbnail list.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Request Body
```json
{
  "selected_main_thumbnail": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg"
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 101,
  "bunny_video_id": "vid_987654321_abc",
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
  ]
}
```

---

### 8. `DELETE /api/v1/videos/{video_id}/thumbnails` — Delete Alternative Thumbnail

Deletes a backup alternative thumbnail asset permanently from Bunny Storage and removes its URL entry from the database.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Request Body
```json
{
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_3.jpg"
}
```

#### Internal Backend Sub-Step: Backend -> Bunny Storage API (Delete File)
* **Purpose**: Issues HTTP `DELETE` to remove `thumb_3.jpg` from Bunny Storage bucket.
* **Method**: `DELETE`
* **Endpoint**: `https://storage.bunnycdn.com/YOUR_STORAGE_ZONE/vid_987654321_abc/thumb_3.jpg`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STORAGE_PASSWORD>
  ```

#### Response Specification (`200 OK`)
```json
{
  "id": 101,
  "bunny_video_id": "vid_987654321_abc",
  "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumbnail.jpg",
  "alt_thumbnail_urls": [
    "https://your-pull-zone.b-cdn.net/vid_987654321_abc/thumb_2.jpg"
  ],
  "message": "Thumbnail deleted successfully"
}
```

---

### 9. `DELETE /api/v1/videos/{video_id}` — Delete Video Asset

Deletes a video asset from the backend database and deletes the underlying container on Bunny Stream.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `video_id` (integer, required): Database primary key ID of the video asset.

#### Internal Backend & External Cloud Workflows

##### Sub-Step A: Backend -> Bunny Stream API (Delete Video Container)
* **Purpose**: Permanently deletes the video container and all encoded video files from Bunny Stream cloud infrastructure.
* **Method**: `DELETE`
* **Endpoint**: `https://video.bunnycdn.com/library/{BUNNY_LIBRARY_ID}/videos/{bunny_video_id}`
* **Headers**:
  ```http
  AccessKey: <BUNNY_STREAM_API_KEY>
  Accept: application/json
  ```
* **Response Body (`200 OK`)**: `OK`

#### Response Specification (`200 OK`)
```json
{
  "status": "success",
  "message": "Video asset 101 dropped successfully."
}
```
