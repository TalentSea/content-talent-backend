---
name: ott-playlist-curation
description: Standards for playlist lifecycle management, video-playlist junction mapping, deterministic cover banners, drag-and-drop video ordering, paginated tracklists, and available video pickers.
---

# OTT Playlist Curation & Management Skill

## Overview
This skill outlines design patterns and data access standards for building high-performance **Playlist Curation Services** within an OTT video platform.

---

## 1. Playlist Data Model & Junction Mapping
- Collections are modeled via `Playlist` and `PlaylistVideo` (ordered junction table with `display_order` and `added_at`).
- Supports atomic drag-and-drop video reordering (`PUT /playlists/{id}/videos/reorder`).

---

## 2. Deterministic Playlist Cover Banners
Playlist cover images use timestamped cloud file paths uploaded via the centralized `image_uploader`:
- Cloud Path: `assets/playlists/pl_{playlist_id}_{timestamp}.{ext}`
- Auto-Purge: Replaces old cover files on Bunny Storage to prevent storage leakage.

---

## 3. Available Video Picker Querying
To populate the admin "Add Videos to Playlist" picker UI:
- Excludes videos already present in the playlist via a `NOT IN` subquery (`PlaylistVideo.select(PlaylistVideo.video_id).where(PlaylistVideo.playlist_id == playlist_id)`).
- Supports case-insensitive title search and pagination.
