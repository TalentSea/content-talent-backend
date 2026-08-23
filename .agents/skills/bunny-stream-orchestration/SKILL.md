---
name: bunny-stream-orchestration
description: Standard operating procedures and guidelines for Bunny Stream video container management, HMAC TUS resumable upload signatures, state machine webhooks (0-10), HLS presigned token URL security, and Bunny Storage asset operations.
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
- Formula: `signature = SHA256(library_id + bunny_api_key + expiration_time + bunny_video_id)`
- Client apps send `AuthorizationSignature`, `AuthorizationExpire`, `VideoId`, and `LibraryId` headers to `https://video.bunnycdn.com/tusupload`.

---

## 2. Webhook State Machine (Status Codes 0–10)

| Status Code | State Action | Backend Action |
| :---: | :--- | :--- |
| `0` | **Queued** | `status = "PENDING"` |
| `1` | **Processing** | `status = "PROCESSING"` |
| `2` | **Encoding** | `status = "ENCODING"` (`encode_progress` < 100) |
| `3` | **Finished** | `status = "READY"` (`encode_progress = 100`) |
| `4` | **Resolution Finished** | `status = "PLAYABLE"` (`is_playable = True`) |
| `5` | **Failed** | `status = "FAILED"` |
| `6` | **PresignedUploadStarted** | Audit log |
| `7` | **PresignedUploadFinished** | `status = "UPLOAD_FINISHED"` |
| `8` | **PresignedUploadFailed** | `status = "UPLOAD_FAILED"` |
| `9` | **CaptionsGenerated** | Store subtitle URLs |
| `10` | **TitleOrDescriptionGenerated** | Store AI metadata |

---

## 3. Presigned HLS & MP4 Stream Security
- Playback URLs use time-bound presigned MD5 tokens valid for 2 hours (`expires_in_seconds = 7200`):
  ```http
  https://your-pull-zone.b-cdn.net/{bunny_video_id}/playlist.m3u8?token=<md5_hash>&expires=<timestamp>
  ```
- Hash Formula: `token = MD5(token_security_key + "/{bunny_video_id}/playlist.m3u8" + expires_timestamp)`
