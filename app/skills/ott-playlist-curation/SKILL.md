---
name: ott-playlist-curation
description: Standards for playlist lifecycle management, video-playlist junction mapping, deterministic cover banner overrides (playlist_{id}.jpg), paginated tracklists, and available video pickers.
---

# OTT Playlist Curation & Management Skill

## Overview
This skill outlines design patterns and data access standards for building high-performance **Playlist Curation Services** within an OTT video platform.

---

## 1. Deterministic Playlist Cover Banners

Playlist cover images use **deterministic cloud file paths** to avoid database URL sprawl and enable instant cloud image overwriting:

- **Path Format**: `assets/playlists/playlist_{playlist_id}.jpg`
- **Public CDN Read URL**: `https://your-pull-zone.b-cdn.net/assets/playlists/playlist_{playlist_id}.jpg`
- **Cloud Write Upload URL**: `https://storage.bunnycdn.com/{storage_zone}/assets/playlists/playlist_{playlist_id}.jpg`

### Overwriting Behavior
Uploading a new cover image via HTTP `PUT` to `image_upload_url` automatically overwrites `playlist_{id}.jpg` on Bunny Storage without requiring prior deletion requests.

---

## 2. API Response Optimization (List vs. Details)

To optimize performance and minimize payload size across mobile networks, Playlist APIs use two distinct DTOs:

### 1. `GET /api/v1/playlists` (List View — `PlaylistSummaryResponse`)
Returns lightweight summary cards containing **`video_count`** instead of heavy video objects:
```json
[
  {
    "id": 104,
    "name": "Trending Sci-Fi",
    "description": "Top sci-fi masterclasses",
    "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
    "video_count": 5
  }
]
```

### 2. `GET /api/v1/playlists/{playlist_id}` (Detail View — `PlaylistResponse`)
Returns full details and a **paginated tracklist** of attached video objects (`videos: [...]`):
```json
{
  "id": 104,
  "name": "Trending Sci-Fi",
  "thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/playlists/playlist_104.jpg",
  "video_count": 45,
  "page": 1,
  "limit": 20,
  "total_pages": 3,
  "videos": [ ... ]
}
```

---

## 3. Junction Mapping & Available Video Picker Query

### Many-to-Many Association
Playlists and Videos are linked via the `PlaylistVideo` junction table featuring a `CompositeKey('playlist', 'video')` and an `order` integer column.

### Available Videos Query (`GET /playlists/{id}/available_videos`)
Used by UI pickers when creators add new videos to a playlist. Executes a subquery returning creator-owned videos that are NOT present in the target playlist junction table:
```python
subquery = PlaylistVideo.select(PlaylistVideo.video).where(PlaylistVideo.playlist == playlist_id)
available_videos = Video.select().where(
    (Video.user == user_id) & 
    (Video.id.not_in(subquery))
).paginate(page, limit)
```
