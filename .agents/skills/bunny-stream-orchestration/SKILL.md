---
name: bunny-stream-orchestration
description: Standard operating procedures and technical guidelines for Bunny Stream video container management, HMAC TUS resumable upload signatures, state machine transcoding webhooks (0-10), HLS and MP4 presigned token URL security, and Bunny Storage asset operations.
---

# Bunny Stream & Cloud Storage Orchestration Skill

## Overview
This skill defines standard operating procedures and technical specifications for integrating **Bunny Stream API** (video container management, TUS uploads, transcoding webhooks, presigned HLS streaming) and **Bunny Storage API** (custom thumbnails, studio logos, and playlist banners).

---

## 1. Security & Authentication Standards

### Master API Key Secrecy
- The master `BUNNY_STREAM_API_KEY` and `BUNNY_STORAGE_PASSWORD` MUST NEVER be exposed to client-side applications.
- All container reservations (`POST /library/{lib}/videos`), deletions, and presigned token calculations MUST occur server-side.

### Client-Side TUS Upload Authorization
For large video files, clients upload directly to Bunny using the TUS resumable protocol:
- **Expiration**: Set to `BUNNY_TUS_UPLOAD_SIGNATURE_EXPIRE_SECONDS` (default: `86400s` / 24 hours).
- **Signature Formula**:
  $$\text{signature} = \text{SHA256}(\text{library\_id} + \text{bunny\_api\_key} + \text{expiration\_timestamp} + \text{bunny\_video\_id})$$
- **Client Request Headers**:
  - `AuthorizationSignature`: The computed SHA-256 hash.
  - `AuthorizationExpire`: Unix expiration timestamp.
  - `VideoId`: Bunny video container ID.
  - `LibraryId`: Bunny video library ID.
  - Endpoint: `https://video.bunnycdn.com/tusupload`

---

## 2. Webhook State Machine (Status Codes 0–10)

Bunny Stream dispatches webhooks to `/api/v1/webhooks/bunny` as transcoding progresses:

| Status Code | State Action | Backend Action |
| :---: | :--- | :--- |
| `0` | **Queued** | `status = "PENDING"` |
| `1` | **Processing** | `status = "PROCESSING"` |
| `2` | **Encoding** | `status = "ENCODING"` (`encode_progress` < 100) |
| `3` | **Finished** | `status = "READY"`, `encode_progress = 100` |
| `4` | **Resolution Finished** | `status = "PLAYABLE"`, `is_playable = True` |
| `5` | **Failed** | `status = "FAILED"`, log failure details |
| `6` | **PresignedUploadStarted** | Audit log |
| `7` | **PresignedUploadFinished** | `status = "UPLOAD_FINISHED"` |
| `8` | **PresignedUploadFailed** | `status = "UPLOAD_FAILED"` |
| `9` | **CaptionsGenerated** | Store subtitle URLs |
| `10` | **TitleOrDescriptionGenerated** | Store AI metadata |

### Idempotency Standard
- Webhook handlers MUST check current video state before updating. If `is_playable` is already `True`, duplicate status `3` or `4` notifications must acknowledge `HTTP 200 OK` without triggering redundant database writes.

---

## 3. Presigned HLS & MP4 Stream Security

Video playback URLs use time-bound presigned MD5 tokens valid for 2 hours (`BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS = 7200`):

### HLS Master Playlist Token
```python
import hashlib
import time

expires = int(time.time()) + settings.BUNNY_HLS_PLAYBACK_URL_EXPIRE_SECONDS
path = f"/{bunny_video_id}/playlist.m3u8"
token_source = f"{settings.BUNNY_STREAM_TOKEN_KEY}{path}{expires}"
token = hashlib.md5(token_source.encode("utf-8")).hexdigest()
hls_url = f"{settings.BUNNY_PULL_ZONE_URL}{path}?token={token}&expires={expires}"
```

### MP4 Offline Download Token
- Path: `/{bunny_video_id}/play_720p.mp4`
- Generated identically using `BUNNY_MP4_DOWNLOAD_URL_EXPIRE_SECONDS`.

---

## 4. Bunny Storage REST API Integration

For non-video binary assets (avatars, thumbnails, logos, banners):
* **Endpoint**: `https://storage.bunnycdn.com/{BUNNY_STORAGE_ZONE_NAME}/{path}`
* **Headers**: `AccessKey: {BUNNY_STORAGE_PASSWORD}`, `Content-Type: application/octet-stream`
* **Upload**: `PUT https://storage.bunnycdn.com/{zone}/{path}`
* **Delete**: `DELETE https://storage.bunnycdn.com/{zone}/{path}`
* **Public CDN Delivery**: Delivered via `BUNNY_STORAGE_PULL_ZONE_URL/{path}` with cache-busting timestamps.
