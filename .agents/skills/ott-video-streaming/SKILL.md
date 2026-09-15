---
name: ott-video-streaming
description: Comprehensive standards for OTT video streaming, playback state synchronization, immutable view event telemetry (VideoViewEvent), zero-trust anti-spam gating, auto-resume positioning, and dynamic popularity ranking algorithms.
---

# OTT Video Streaming, Playback Telemetry & Zero-Trust Anti-Spam Skill

## Overview
This skill outlines the architecture, security models, and implementation guidelines for video streaming playback, subscriber watch progress synchronization, creator view telemetry, and anti-spam verification in the FastAPI + Peewee backend.

---

## 1. Architectural Separation: Telemetry vs. Personal Playback

A fundamental architectural principle of this platform is the **strict decoupling of creator view telemetry from subscriber personal playback state**:

```
┌────────────────────────────────────────────────────────┐
│               Subscriber Action on Mobile              │
└──────────────────────────┬─────────────────────────────┘
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
 ┌───────────────────────┐   ┌───────────────────────┐
 │   Personal Playback   │   │   Creator Telemetry   │
 │    (WatchHistory)     │   │   (VideoViewEvent)    │
 ├───────────────────────┤   ├───────────────────────┤
 │ • Mutable per (vid,sub│   │ • Immutable append-   │
 │ • Current scrub pos   │   │   only event log      │
 │ • Continue watching   │   │ • Audit trail         │
 │ • Safe to clear/reset │   │ • Survives user clear │
 └───────────────────────┘   └───────────────────────┘
```

1. **`WatchHistory` (Personal Playback)**:
   - Tracks `last_position_seconds`, `completed`, and `last_watched_at`.
   - Has a composite unique constraint: `UNIQUE(video_id, subscriber_id)`.
   - Can be cleared or individual items removed by the subscriber at any time without impacting creator analytics.
2. **`VideoViewEvent` (Immutable View Telemetry)**:
   - Records discrete, legitimate view milestones: `(video_id, creator_id, subscriber_id, created_at)`.
   - Never deleted when subscribers clear their personal watch history.
   - Powers admin dashboard date-window analytics and anti-spam gating.

---

## 2. Playback Progress Sync Protocol (`POST /{id}/progress`)

Mobile video players synchronize playback state using `POST /api/v1/mobile/videos/{video_id}/progress`.

### Deterministic 4-Milestone Calling Schedule
To eliminate frontend guesswork and race conditions, client players must dispatch this endpoint at four deterministic milestones:
1. **Playback Start / Resume**: Immediately upon video start (`progress_seconds = 0` or initial resume point).
2. **Periodic Interval (10s)**: Every **10 seconds** during continuous streaming playback.
3. **Watch Threshold Milestone**: The exact second playback crosses the configured threshold (`VIDEO_VIEW_WATCH_THRESHOLD_PERCENT` of duration, e.g., 30%). Immediately after this sync completes, the player triggers `POST /{video_id}/views`.
4. **Lifecycle Events**: On player pause, seek/scrub release, app backgrounding, screen exit (`dispose()`), or completion ($\ge 95\%$).

### Backend Completion & Continue Watching Invariants
* **Completion**: When `(progress_seconds / duration) * 100 >= VIDEO_COMPLETION_THRESHOLD_PERCENT` (default: `95.0%`), mark `completed = True`. Completed videos are automatically filtered out of the "Continue Watching" carousel.
* **Continue Watching Feed**: Unfinished videos (`completed == False`) are eligible for "Continue Watching" only if `last_position_seconds >= CONTINUE_WATCHING_MIN_SECONDS` (default: `10s`).

---

## 3. Zero-Trust Anti-Spam View Gatekeeper (`POST /{id}/views`)

`POST /api/v1/mobile/videos/{video_id}/views` credits legitimate views to videos and creators. The backend independently verifies **four strict gates** before accepting a view:

```
[Incoming POST /views Request]
               │
               ▼
   [ Gate 1: Role == 'subscriber'? ] ──── No ───► HTTP 403 Forbidden
               │ Yes
               ▼
   [ Gate 2: WatchHistory >= Threshold? ] ─ No ─► HTTP 400 Bad Request
               │ Yes
               ▼
   [ Gate 3: Cooldown Window Passed? ] ─── No ───► Return Current Views (Debounced)
               │ Yes
               ▼
   [ Gate 4: Under Daily View Cap? ] ───── No ───► Return Current Views (Capped)
               │ Yes
               ▼
   [ Log VideoViewEvent + Atomic Increment views & popularity_score ]
```

### Gatekeeper Rules & Status Codes
1. **Gate 1: Role Enforcement**:
   - Strictly requires `role == 'subscriber'`.
   - Anonymous guest tokens (`role == 'guest'`) are rejected with `HTTP 403 Forbidden` (`"Subscriber access required to record views"`).
2. **Gate 2: Server-Side Watch Progress Verification**:
   - Queries `WatchHistory` for `(video_id, subscriber_id)`.
   - Verifies: `history.last_position_seconds >= (duration_seconds * VIDEO_VIEW_WATCH_THRESHOLD_PERCENT / 100.0)`.
   - If threshold is not met, rejects with `HTTP 400 Bad Request ("WATCH_THRESHOLD_NOT_MET")`. Never trust client-reported view counts.
3. **Gate 3: Session Cooldown Debounce**:
   - Queries `VideoViewEvent` for any view by this subscriber for this video within the last `VIDEO_VIEW_COOLDOWN_MINUTES` (default: `30` mins).
   - If present, treats as the same continuous viewing session and returns current count without incrementing.
4. **Gate 4: Rolling Daily Cap**:
   - Counts `VideoViewEvent` for this subscriber and video within `now - timedelta(hours=VIDEO_VIEW_DAILY_WINDOW_HOURS)` (default: `24` hours).
   - If `count >= VIDEO_VIEW_MAX_DAILY_PER_USER` (default: `3`), returns current count without incrementing.
5. **View Credit**:
   - Atomically creates `VideoViewEvent`.
   - Increments `video.views += 1`.
   - Updates `popularity_score = video.views + (POPULARITY_SCORE_LIKE_WEIGHT * likes)`.

---

## 4. Popularity Scoring Algorithm

Videos maintain a pre-calculated, B-Tree indexed `popularity_score` column:

$$\text{popularity\_score} = \text{views} + (\text{POPULARITY\_SCORE\_LIKE\_WEIGHT} \times \text{likes})$$

* **Default Weight**: `POPULARITY_SCORE_LIKE_WEIGHT = 3`.
* **Atomic Updates**: Recalculated and saved whenever:
  1. A legitimate view is credited in `increment_view_count`.
  2. A subscriber toggles a like in `toggle_video_like`.
* **Catalog Ordering**: Enables instant, indexed sorting for `GET /api/v1/mobile/videos?sort=popular` via:
  ```python
  query = query.order_by(Video.popularity_score.desc(), Video.id.desc())
  ```

---

## 5. Environment Settings Reference

All decision parameters MUST be loaded from `app.config.get_settings()` and NEVER hardcoded:

| Setting Key | Type | Default | Purpose |
| :--- | :---: | :---: | :--- |
| `VIDEO_VIEW_WATCH_THRESHOLD_PERCENT` | `float` | `30.0` | Minimum % of duration watched before view eligibility. |
| `VIDEO_VIEW_COOLDOWN_MINUTES` | `int` | `30` | Minimum minutes between views counted from same subscriber. |
| `VIDEO_VIEW_MAX_DAILY_PER_USER` | `int` | `3` | Maximum views counted per subscriber per video per 24h. |
| `VIDEO_VIEW_DAILY_WINDOW_HOURS` | `int` | `24` | Rolling window hours for daily view cap evaluation. |
| `VIDEO_COMPLETION_THRESHOLD_PERCENT` | `float` | `95.0` | Threshold % marking video fully watched (`completed = True`). |
| `CONTINUE_WATCHING_MIN_SECONDS` | `int` | `10` | Minimum seconds watched before appearing in Continue Watching. |
| `POPULARITY_SCORE_LIKE_WEIGHT` | `int` | `3` | Multiplier weight for likes in popularity calculation. |
