---
name: bunny-stream-orchestration
description: Standard operating procedures and guidelines for Bunny Stream video container management, HMAC TUS resumable upload signatures, state machine webhooks (0-10), HLS presigned token URL security, and Bunny Storage thumbnail operations.
---

# Bunny Stream & Cloud Storage Orchestration Skill

## Overview
This skill defines standard operating procedures and technical specifications for integrating **Bunny Stream API** (video container management, TUS uploads, transcoding webhooks, presigned HLS streaming) and **Bunny Storage API** (alternative cover thumbnails and deterministic playlist banners).

---

## 1. Security & Authentication Standards

### Master API Key Secrecy
- **Rule**: The master `BUNNY_STREAM_API_KEY` and `BUNNY_STORAGE_PASSWORD` MUST NEVER be exposed to public web browsers, mobile apps, or client-side code.
- **Enforcement**: All cloud container reservations (`POST /library/{lib}/videos`), deletion requests (`DELETE /library/{lib}/videos/{id}`), and presigned signature calculations MUST take place on the backend server.

### Client-Side TUS Upload Authorization
- **Formula**: `signature = SHA256(library_id + bunny_api_key + expiration_time + bunny_video_id)`
- **Header Injection**: Client apps send `AuthorizationSignature`, `AuthorizationExpire`, `VideoId`, and `LibraryId` headers to `https://video.bunnycdn.com/tusupload`.

---

## 2. Webhook State Machine Handling

Bunny Stream calls `POST /api/v1/webhooks/bunny` with the JSON body `{ "VideoLibraryId": 123456, "VideoGuid": "guid", "Status": <int> }`.

### Status Mapping Reference

| Status Code | Status Name | State Action | Backend Action |
| :---: | :--- | :--- | :--- |
| `0` | **Queued** | `status = "PENDING"` | Video queued in GPU pipeline |
| `1` | **Processing** | `status = "PROCESSING"` | Extracting audio/frame preview |
| `2` | **Encoding** | `status = "ENCODING"` | Encoding active (`encode_progress` < 100) |
| `3` | **Finished** | `status = "READY"` | All resolutions ready (`encode_progress = 100`) |
| `4` | **Resolution Finished** | `status = "PLAYABLE"` | First resolution (240p) ready (`is_playable = True`) |
| `5` | **Failed** | `status = "FAILED"` | Corrupt video codec/format |
| `6` | **PresignedUploadStarted** | Event Audit | Log upload session start |
| `7` | **PresignedUploadFinished** | `status = "UPLOAD_FINISHED"` | Bytes received by Bunny |
| `8` | **PresignedUploadFailed** | `status = "UPLOAD_FAILED"` | Upload interrupted |
| `9` | **CaptionsGenerated** | Metadata Update | Store WebVTT subtitle track URLs |
| `10` | **TitleOrDescriptionGenerated** | Metadata Update | Store AI-generated title/description |

---

## 3. Dedicated Thumbnail 0-Indexed Slot Routing

Thumbnail uploads follow a 0-indexed slot routing model (`slot: 0, 1, 2`):

- **Slot 0 (Main Cover)**:
  - Upload Target: Bunny Stream API (`PUT https://video.bunnycdn.com/library/{lib_id}/videos/{bunny_video_id}/thumbnail`)
  - CDN Read URL: `https://your-pull-zone.b-cdn.net/{bunny_video_id}/thumbnail.jpg`
- **Slot 1 (Alt Cover 1)**:
  - Upload Target: Bunny Storage API (`PUT https://storage.bunnycdn.com/{storage_zone}/{bunny_video_id}/thumb_2.jpg`)
  - CDN Read URL: `https://your-pull-zone.b-cdn.net/{bunny_video_id}/thumb_2.jpg`
- **Slot 2 (Alt Cover 2)**:
  - Upload Target: Bunny Storage API (`PUT https://storage.bunnycdn.com/{storage_zone}/{bunny_video_id}/thumb_3.jpg`)
  - CDN Read URL: `https://your-pull-zone.b-cdn.net/{bunny_video_id}/thumb_3.jpg`

---

## 4. Presigned HLS Stream Security

Raw playback URLs must never be exposed permanently. Playback URLs must use time-bound presigned tokens valid for 2 hours (`expires_in_seconds = 7200`):

```http
https://your-pull-zone.b-cdn.net/{bunny_video_id}/playlist.m3u8?token=<md5_hash>&expires=<timestamp>
```

- **Hash Formula**: `token = MD5(token_security_key + "/{bunny_video_id}/playlist.m3u8" + expires_timestamp)`
