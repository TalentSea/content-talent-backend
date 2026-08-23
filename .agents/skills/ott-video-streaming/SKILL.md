---
name: ott-video-streaming
description: Guidelines for video streaming feeds, high-frequency 10-second playback progress synchronization, auto-resume positioning, atomic popularity score calculation (views + 3*likes), and subscriber RBAC.
---

# OTT Video Streaming & Playback Subsystem Skill

## Overview
This skill documents real-time video playback synchronization, watch history lifecycle, and engagement scoring algorithms for OTT streaming backends.

---

## 1. High-Frequency Playback Progress Sync
- Mobile players send periodic heartbeat progress pings (`POST /api/v1/mobile/videos/{id}/progress`) with `current_time` and `duration`.
- Automatically tracks `completed = True` when `current_time / duration >= 0.95`.
- Powers `GET /api/v1/mobile/videos/continue-watching` and `GET /api/v1/mobile/videos/history`.

---

## 2. Indexed Popularity Ranking Algorithm
- Engagement popularity is computed via `popularity_score = views + (3 * likes)`.
- Stored on a B-Tree indexed database column `popularity_score` and atomically updated on view or like events.
- Enables sub-millisecond catalog ordering (`GET /videos?sort=popular`).

---

## 3. Subscriber Role-Based Access Control (RBAC)
- **Public / Guest Access**: Allows browsing video catalogs, category feeds, and public metadata (`get_current_user`).
- **Subscriber-Only Access**: Enforces `role == "subscriber"` (`get_current_subscriber`) for presigned HLS streaming master playlists and offline MP4 download tokens.
