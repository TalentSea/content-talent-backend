---
name: ott-playlist-curation
description: Technical standards for playlist lifecycle management, video-playlist junction mapping, deterministic cover banners, drag-and-drop video ordering, paginated tracklists, and available video pickers.
---

# OTT Playlist Curation & Management Skill

## Overview
This skill outlines design patterns and data access standards for building high-performance **Playlist Curation Services** within an OTT video platform.

---

## 1. Playlist Data Model & Junction Architecture

Playlists are modeled as creator-owned collections containing an ordered sequence of ready videos:

```
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│        Playlist        │      │     PlaylistVideo      │      │         Video          │
├────────────────────────┤      ├────────────────────────┤      ├────────────────────────┤
│ • title, description   │      │ • playlist (FK)        │      │ • title, duration      │
│ • cover_url            │◄─────┤ • video (FK)           │─────►│ • views, popularity    │
│ • creator (FK)         │      │ • display_order (int)  │      │ • status == 'published'│
│ • is_active (bool)     │      │ • added_at (datetime)  │      │ • is_playable == True  │
└────────────────────────┘      └────────────────────────┘      └────────────────────────┘
```

### Constraints & Indexes
* **Unique Pair Constraint**: `UNIQUE(playlist_id, video_id)` prevents accidental duplicate inclusions of the same video in a single playlist.
* **Composite Index**: `(playlist_id, display_order)` ensures instantaneous ordered retrieval of tracklists.

---

## 2. Drag-and-Drop Batch Reordering

Admins can rearrange the tracklist order via `PUT /api/v1/admin/playlists/{playlist_id}/videos/reorder`:

### Implementation Standard
Reordering operations MUST run within an atomic database transaction to prevent corrupt ordering states:
```python
with db_proxy.atomic():
    for item in payload.video_orders:  # List of { "video_id": int, "display_order": int }
        PlaylistVideo.update(display_order=item.display_order).where(
            (PlaylistVideo.playlist == playlist_id)
            & (PlaylistVideo.video == item.video_id)
        ).execute()
```

---

## 3. "Available Video Picker" Querying

The admin UI needs to display videos available to add to a playlist, strictly excluding videos already in that playlist:

### Subquery Anti-Join Standard
```python
existing_video_ids = (
    PlaylistVideo.select(PlaylistVideo.video_id)
    .where(PlaylistVideo.playlist_id == playlist_id)
)

query = Video.select().where(
    (Video.user == creator_id)
    & (Video.id.not_in(existing_video_ids))
    & (fn.LOWER(Video.status).in_(["published", "ready"]))
    & (Video.is_playable == True)
)

if search:
    query = query.where(Video.title.contains(search))

total_count = query.count()
videos = list(query.order_by(Video.created_at.desc()).paginate(page, limit))
```

---

## 4. Deterministic Playlist Cover Banners

Playlist covers MUST use the centralized `image_uploader` utility:
* **Cloud Path**: `assets/playlists/pl_{playlist_id}_{int(time.time())}.webp`
* **Size Enforcement**: `settings.MAX_PLAYLIST_COVER_SIZE_MB` (default: `5 MB`).
* **Auto-Cleanup**: Pass `old_file_url=playlist.cover_url` to purge the replaced asset on Bunny Storage.
