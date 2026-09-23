---
name: creator-studio-analytics-and-curation
description: Guidelines and architectural rules for Creator Admin Studio operations, including honest date-window analytics querying VideoViewEvent, automated video publishing workers, featured video curation, comment moderation, category reordering, and branding customization.
---

# Creator Studio Analytics, Curation & Automation Skill

## Overview
This skill establishes standards for building and maintaining Creator Admin Studio features in the OTT platform, focusing on creator-isolated analytics, background automation, catalog curation, and studio customization.

---

## 1. Studio Analytics Dashboard & Honest Window Telemetry

The Creator Dashboard (`GET /api/v1/admin/dashboard`) provides real-time and windowed telemetry for creator business monitoring.

### Core Metrics & Data Sources
* **Total / Windowed Views**: Queried exclusively from the immutable `VideoViewEvent` ledger where `tenant == tenant_id AND created_at BETWEEN start_date AND end_date`.
* **Total Subscribers**: Count of subscribers linked to this creator.
* **Watch Time**: Aggregated seconds streamed across creator assets.
* **Top Performing Videos**: Ranked by views within the selected date window or by indexed `popularity_score`.

### Honest Window Calculation Standard
* **No Fallbacks**: If a creator has `0` views in the requested date range, the service MUST report `0` views and `0.0%` growth. Never fall back to lifetime views or mock numbers.
* **Growth Rate Formula**:
  $$\text{growth\_pct} = \begin{cases} \left(\frac{\text{current} - \text{previous}}{\text{previous}}\right) \times 100 & \text{if } \text{previous} > 0 \\ 0.0 & \text{if } \text{previous} = 0 \end{cases}$$
* **ISO Date Parsing**: Always use `date.fromisoformat(str)` rather than `datetime.strptime().date()` to ensure clean Ruff linting (`DTZ007`) and optimal performance.

---

## 2. Automated Scheduled Video Publisher

Creators can schedule future video releases by providing an IST release timestamp (`status = "scheduled"`, `scheduled_at = datetime`).

### Background Automation Loop
* **Task**: `scheduled_video_auto_publisher()` runs inside the FastAPI lifespan context.
* **Interval**: Configured via `AUTO_PUBLISHER_LOOP_INTERVAL_SECONDS` (default: `60s`).
* **Atomic Publication Logic**:
  ```python
  now = datetime.now(timezone.utc)
  active_creators = Admin.select(Admin.id).where(Admin.is_active == True)
  due_videos = Video.update(
      status="published",
      published_at=Video.scheduled_at,
      scheduled_at=None,
  ).where(
      (Video.status == "scheduled")
      & (Video.scheduled_at.is_null(False))
      & (Video.scheduled_at <= now)
      & (Video.user.in_(active_creators))
  ).execute()
  ```
* **Guardrail**: Only scheduled videos of active (`Admin.is_active == True`) creators are published. If a creator account is deactivated or suspended by platform administrators, their scheduled releases remain dormant.

---

## 3. Featured Videos Curation Subsystem

Creators curate home carousel featured items via `/api/v1/admin/featured-videos`:

1. **Capacity Limit**: Enforce `MAX_FEATURED_VIDEOS_PER_CREATOR` (default: `10`). If a creator attempts to feature more than this limit, reject with `HTTP 400 Bad Request`.
2. **Display Order**: Store `position` (1-indexed integer) to maintain deterministic ordering in mobile hero banners.
3. **Status Guardrail**: Both published/ready status and playback readiness MUST be combined with logical AND (`&`):
   `(fn.LOWER(Video.status).in_(["published", "ready"])) & (Video.is_playable == True)`
   Never use bitwise OR (`|`), which would prematurely leak draft or scheduled videos into featured slots before release.

---

## 4. Category Management & Reordering

Categories organize video catalogs into navigable feeds:
* **Display Ordering**: Support bulk reordering (`PUT /categories/reorder`) with atomic batch updates.
* **Cascade Handling on Deletion**: When deleting a category, ensure videos assigned to that category have their `category` field safely set to `None` or an "Uncategorized" fallback to prevent dangling references.

---

## 5. Comment Moderation

Subscriber comments on videos are moderated via `/api/v1/admin/comments`:
* **Hierarchical Replies**: Comments support nested threading via self-referential `parent_id` foreign keys.
* **Pinning**: Creators can pin top comments (`is_pinned = True`). Only one comment per video may be pinned at a time.
* **Soft Deletion**: Moderated or deleted comments set `is_deleted = True` to preserve reply thread integrity while censoring content.

---

## 6. Studio Branding & Theming

Studio visual identity is managed via `/api/v1/admin/branding`:
* **Colors**: Store hexadecimal palette values (`primary_color`, `secondary_color`, `accent_color`, `background_color`).
* **Media Assets**: Logo and hero banners are uploaded using the centralized `image_uploader`, enforcing `MAX_LOGO_SIZE_MB` and `MAX_BANNER_SIZE_MB` with automatic replacement cleanup.

---

## 7. Creator Ad Monetization, Settlements & Bank Settings

Creator advertising revenue telemetry, monthly payouts, and bank profiles are managed via `/api/v1/admin/monetization`:
* **Earnings & KPI Summary (`GET /summary`)**: Active month impressions, dynamic historical eCPM rate, expected payout schedule (28th of next month), and pending/last payout cards.
* **Interactive Time-Series Charts (`GET /analytics`)**: Granular daily, weekly, and monthly data points for impressions and net earnings.
* **Historical Settlement Ledger (`GET /settlements`)**: Paginated statement history with bank wire UTR references and invoice URLs.
* **Bank Payout Profile (`GET / PUT /settings`)**: Masked account numbers (`••••••••4589`), IFSC code validation, and bank institution auto-resolution on write.
* **Detailed Playbook**: For complete reconciliation, anti-spam telemetry, and commission architecture, reference the dedicated `ad-monetization-and-settlements` skill.

---

## 8. Environment Configuration Reference

| Environment Variable | Type | Default | Purpose |
| :--- | :---: | :---: | :--- |
| `AUTO_PUBLISHER_LOOP_INTERVAL_SECONDS` | `int` | `60` | Polling frequency for publishing due scheduled videos. |
| `MAX_FEATURED_VIDEOS_PER_CREATOR` | `int` | `10` | Maximum featured videos a single creator can curate. |
| `MAX_LOGO_SIZE_MB` | `int` | `5` | Maximum upload size for studio branding logos. |
| `MAX_BANNER_SIZE_MB` | `int` | `10` | Maximum upload size for studio hero banners. |
| `PLATFORM_AD_COMMISSION_PERCENT` | `float` | `30.0` | Platform retained technology commission on ad revenue. |
| `PAYOUT_DAY_OF_MONTH` | `int` | `28` | Day of following month when creator wire disbursements occur. |
| `MIN_PAYOUT_THRESHOLD` | `float` | `500.0` | Minimum net earnings (₹) required to trigger a disbursement. |
