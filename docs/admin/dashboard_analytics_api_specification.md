# Admin Studio Dashboard & Analytics API Specification

This document details the RESTful API endpoints for Web Admin Creators to view, analyze, and monitor their Studio Dashboard metrics in real time, powering the high-performance dark-themed Creator Studio UI.

---

## 1. System Architecture & Security Standards

### 1.1 Base Route Prefix

```http
/api/v1/admin/dashboard
```

### 1.2 Authentication & Authorization

- All dashboard endpoints are protected and require a valid Admin Creator JWT Bearer token passed in the request header:

```http
Authorization: Bearer <admin_access_token>
```

- **Strict Multi-Tenant Isolation**: The authenticated creator's `user_id` is extracted strictly from the JWT context via `CurrentAdmin`. Every metric, revenue calculation, view count, and subscriber listing is filtered by `creator_id` to guarantee zero cross-tenant data leakage.

### 1.3 Localization & Metric Standards

- **Default Currency**: `"INR"` (Indian Rupee ₹) matching the platform's Razorpay payment infrastructure.
- **Timestamp Standard**: All audit and transaction timestamps are stored in UTC and ISO 8601 formatted (`YYYY-MM-DDTHH:MM:SSZ`).
- **Zero N+1 Query Guarantee**: All aggregations are computed directly at the database engine level using indexed columns and native SQL functions (`fn.SUM`, `fn.COUNT`, `fn.GROUP_BY`).

---

## 2. Standard HTTP Error Responses

All error responses adhere to the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid Query Parameter

```json
{
  "detail": "Invalid period '1y'. Supported periods are: '7d', '30d', '90d', '6m'."
}
```

#### 2. `401 Unauthorized` — Missing or Expired JWT Token

```json
{
  "detail": "Could not validate credentials"
}
```

#### 3. `500 Internal Server Error` — Database / Aggregation Failure

```json
{
  "detail": "Failed to compute dashboard telemetry metrics"
}
```

---

## 3. Detailed Endpoint Specifications

```
Studio Dashboard Endpoints:
├── 3.1 GET /api/v1/admin/dashboard/stats                  (Top 5 KPI Metric Cards)
├── 3.2 GET /api/v1/admin/dashboard/analytics            (Revenue & Subscriber Growth Area Chart)
├── 3.3 GET /api/v1/admin/dashboard/subscription-breakdown(Subscription Tier Donut / Pie Chart)
├── 3.4 GET /api/v1/admin/dashboard/recent-activity       (Recent Users & Mobile Subscribers Feed)
└── [Existing] GET /api/v1/admin/videos                   (Top Content Feed via ?status=published&sort=views)
```

---

### 3.1 `GET /api/v1/admin/dashboard/stats` — KPI Overview Cards

Retrieves high-level summary cards displayed across the top row of the studio dashboard, complete with dynamic date range selection and period-over-period growth telemetry.

#### Headers

```http
Authorization: Bearer <admin_access_token>
```

#### Query Parameters

- `range` _(string, optional, default: `"30d"`)_: Quick preset selection window.
  - `"7d"`: Past 7 days vs. previous 7 days.
  - `"30d"`: Past 30 days vs. previous 30 days (default).
  - `"90d"`: Past 90 days vs. previous 90 days.
  - `"12m"`: Past 12 months vs. previous 12 months.
- `start_date` _(date, optional, format: `YYYY-MM-DD`)_: Custom start date for arbitrary calendar pickers.
- `end_date` _(date, optional, format: `YYYY-MM-DD`)_: Custom end date for arbitrary calendar pickers.

> **Resolution Priority**: If `start_date` and `end_date` are both provided, the backend computes metrics across that exact custom date window. Otherwise, it defaults to the `range` preset.

#### Response Envelope (`200 OK`)

```json
{
  "start_date": "2026-08-10",
  "end_date": "2026-09-09",
  "currency": "INR",
  "total_revenue": {
    "current": 45231.0,
    "previous": 36740.0,
    "growth_percentage": 23.1
  },
  "total_views": {
    "current": 2400000,
    "previous": 2429150,
    "growth_percentage": -1.2
  },
  "total_users": {
    "current": 18920,
    "previous": 17454,
    "growth_percentage": 8.4
  },
  "total_subscribers": {
    "current": 12543,
    "previous": 11119,
    "growth_percentage": 12.8
  },
  "total_content": {
    "total": 48,
    "published": 45,
    "drafts": 3,
    "recently_added": 2
  }
}
```

#### Field Definitions

- `start_date`, `end_date`: Exact ISO date boundary resolved for this calculation.
- `currency`: Default currency code (`"INR"`).
- `total_revenue`: Sum of captured payments in ₹ INR with period-over-period growth.
- `total_views`: Sum of video views with period-over-period growth.
- `total_users`: Total registered audience accounts with user acquisition growth.
- `total_subscribers`: Paying members with an active subscription (`status = 'active'`) and conversion growth.
- `total_content`: Catalog inventory breakdown:
  - `total`: All lifetime video assets.
  - `published`: Ready and playable videos visible on the platform.
  - `drafts`: Processing, scheduled, or unlisted videos.
  - `recently_added`: New videos uploaded during the selected date window.

#### Mathematical Telemetry Model (Growth Percentage)

The growth percentage badge on velocity metrics compares the selected window against the immediately preceding period of identical duration:

1. **Current Window ($V_{\text{current}}$)**: $[\text{start\_date},\; \text{end\_date}]$ with duration $D = \text{end\_date} - \text{start\_date}$.
2. **Previous Window ($V_{\text{previous}}$)**: $[\text{start\_date} - D,\; \text{start\_date})$

$$\text{Growth \%} = \left( \frac{V_{\text{current}} - V_{\text{previous}}}{V_{\text{previous}}} \right) \times 100$$

##### Division-by-Zero & Edge Case Rules:

| Condition                                              | Growth Value                                | Explanation                             |
| ------------------------------------------------------ | ------------------------------------------- | --------------------------------------- |
| $V_{\text{previous}} = 0 \land V_{\text{current}} > 0$ | `+100.0%`                                   | Brand-new positive metric baseline      |
| $V_{\text{previous}} = 0 \land V_{\text{current}} = 0$ | `0.0%`                                      | Inactive / no activity in either window |
| $V_{\text{previous}} > 0 \land V_{\text{current}} = 0$ | `-100.0%`                                   | Complete churn / volume drop            |
| $V_{\text{previous}} > 0 \land V_{\text{current}} > 0$ | Standard formula rounded to 1 decimal place | e.g. `+23.1%`, `-1.2%`                  |

##### Concrete Calculation Examples:

- **Monthly Revenue (`+23.1%`)**:
  $$V_{\text{prev}} = ₹36,740.00,\quad V_{\text{curr}} = ₹45,231.00 \implies \left(\frac{45231 - 36740}{36740}\right) \times 100 = \mathbf{+23.1\%}$$
- **Total Views (`-1.2%`)**:
  $$V_{\text{prev}} = 2,429,150,\quad V_{\text{curr}} = 2,400,000 \implies \left(\frac{2400000 - 2429150}{2429150}\right) \times 100 = \mathbf{-1.2\%}$$

---

### 3.2 `GET /api/v1/admin/dashboard/analytics` — Visual Time-Series Analytics Chart

Returns grouped time-series telemetry points powering visual line, area, or bar charts on the dashboard. Supports presets or custom calendar ranges with automatic or explicit interval bucketing.

#### Headers

```http
Authorization: Bearer <admin_access_token>
```

#### Query Parameters

- `range` _(string, optional, default: `"6m"`)_: Quick preset selection window (`"7d"`, `"30d"`, `"90d"`, `"6m"`, `"12m"`).
- `start_date` _(date, optional, format: `YYYY-MM-DD`)_: Custom start date.
- `end_date` _(date, optional, format: `YYYY-MM-DD`)_: Custom end date.
- `interval` _(string, optional, values: `"day"`, `"week"`, `"month"`)_: Date grouping frequency. If omitted, automatically determined from the date range:

##### Interval Auto-Resolution Matrix:

| Total Duration ($D = \text{end} - \text{start}$) | Auto-Selected `interval` | Typical Points  |
| ------------------------------------------------ | ------------------------ | --------------- |
| $D \le 30\text{ days}$ (e.g. `7d`, `30d`)        | `"day"`                  | 7 to 30 points  |
| $31 \le D \le 90\text{ days}$ (e.g. `90d`)       | `"week"`                 | ~8 to 13 points |
| $D \ge 91\text{ days}$ (e.g. `6m`, `12m`)        | `"month"`                | 6 to 12 points  |

#### Response Envelope (`200 OK`)

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-06-30",
  "interval": "month",
  "currency": "INR",
  "data_points": [
    {
      "date": "2026-01-01",
      "label": "Jan",
      "users": 2800,
      "subscribers": 1400,
      "revenue": 12500.0,
      "views": 320000
    },
    {
      "date": "2026-02-01",
      "label": "Feb",
      "users": 3400,
      "subscribers": 2200,
      "revenue": 18400.0,
      "views": 410000
    },
    {
      "date": "2026-03-01",
      "label": "Mar",
      "users": 4900,
      "subscribers": 3500,
      "revenue": 24900.0,
      "views": 530000
    },
    {
      "date": "2026-04-01",
      "label": "Apr",
      "users": 6800,
      "subscribers": 5100,
      "revenue": 31200.0,
      "views": 620000
    },
    {
      "date": "2026-05-01",
      "label": "May",
      "users": 9500,
      "subscribers": 7800,
      "revenue": 38000.0,
      "views": 710000
    },
    {
      "date": "2026-06-01",
      "label": "Jun",
      "users": 14200,
      "subscribers": 12543,
      "revenue": 45231.0,
      "views": 850000
    }
  ]
}
```

#### Field Definitions

- `start_date`, `end_date`: Exact ISO boundary resolved.
- `interval`: Grouping unit applied (`"day"`, `"week"`, or `"month"`).
- `data_points`: Ordered chronological array of bucketed points:
  - `date`: ISO boundary date for machine sorting and tooltip popups (`"2026-06-01"`).
  - `label`: Human-readable label for chart X-axis rendering (`"Jun"`).
  - `users`: New user registrations during that interval.
  - `subscribers`: Total active paid subscribers as of that interval.
  - `revenue`: Captured revenue in ₹ INR during that interval.
  - `views`: Video plays accumulated during that interval.

---

### 3.3 `GET /api/v1/admin/dashboard/subscription-breakdown` — Donut / Pie Chart

Returns subscriber distribution and actual captured revenue grouped by subscription plan tier for the selected date window, empowering the frontend to render donut charts by either subscribers or revenue.

#### Business Logic & Data Fidelity

- **Date Filtering**: Accepts `range` presets or custom `start_date` and `end_date` calendar boundaries, keeping the donut chart dynamically synchronized with the dashboard date filter.
- **Dual Telemetry (Subscribers & Revenue)**: Each tier provides both `subscribers` count with `subscribers_percentage` and period `revenue` with `revenue_percentage`, enabling zero-cost frontend toggling between **"By Subscribers"** and **"By Revenue"**.
- **Strict Plan Name Uniqueness**: In the database, every plan name is guaranteed unique per creator.
- **Active Plans (`is_active: true`)**: Current tiers available for new purchases appear with their configured name and badge text.
- **Retired / Deactivated Plans (`is_active: false`)**: If a plan was deactivated but still generated revenue or contains subscribers within their valid access window, it is returned with its **exact real name and `plan_id`**, preserving 100% data fidelity. The frontend uses `is_active: false` to visually style it (e.g. gray slice or "Archived" pill).
- **`badge_text` Field Integrity**: The backend **never** forces `badge_text` to `null` or overrides it with `"Archived"`. If the creator configured a badge (e.g. `"Founder Offer"`), that exact string is returned regardless of active state. If the creator left it empty, it remains `null`. Active/inactive state is strictly governed by `is_active: true | false`.
- **Zero Clutter**: Tiers with zero subscribers and zero revenue in the selected window that are also inactive do not appear.

#### Headers

```http
Authorization: Bearer <admin_access_token>
```

#### Query Parameters

- `range` _(string, optional, default: `"30d"`)_: Quick preset selection window (`"7d"`, `"30d"`, `"90d"`, `"12m"`).
- `start_date` _(date, optional, format: `YYYY-MM-DD`)_: Custom start date.
- `end_date` _(date, optional, format: `YYYY-MM-DD`)_: Custom end date.

#### Response Envelope (`200 OK`)

```json
{
  "start_date": "2026-06-11",
  "end_date": "2026-09-09",
  "currency": "INR",
  "total_subscribers": 12543,
  "total_revenue": 135693.0,
  "tiers": [
    {
      "plan_id": 1,
      "name": "Pro Yearly",
      "badge_text": "Most Popular",
      "is_active": true,
      "subscribers": 6898,
      "subscribers_percentage": 55.0,
      "revenue": 82776.0,
      "revenue_percentage": 61.0
    },
    {
      "plan_id": 2,
      "name": "Standard Monthly",
      "badge_text": null,
      "is_active": true,
      "subscribers": 3762,
      "subscribers_percentage": 30.0,
      "revenue": 40707.0,
      "revenue_percentage": 30.0
    },
    {
      "plan_id": 3,
      "name": "Starter",
      "badge_text": null,
      "is_active": true,
      "subscribers": 1505,
      "subscribers_percentage": 12.0,
      "revenue": 8140.0,
      "revenue_percentage": 6.0
    },
    {
      "plan_id": 4,
      "name": "Early Bird",
      "badge_text": "Limited Offer",
      "is_active": false,
      "subscribers": 378,
      "subscribers_percentage": 3.0,
      "revenue": 4070.0,
      "revenue_percentage": 3.0
    }
  ]
}
```

#### Field Definitions

- `start_date`, `end_date`: Exact ISO date boundary resolved for this calculation.
- `currency`: Default currency code (`"INR"`).
- `total_subscribers`: Total count of active subscribers across all tiers (used for donut center text).
- `total_revenue`: Total captured revenue in ₹ INR across all tiers during the selected period (used for donut center text).
- `tiers`: Array of subscription tier segments:
  - `plan_id`: Database ID of the subscription plan.
  - `name`: Real name of the plan (e.g. `"Pro Yearly"`).
  - `badge_text`: Custom creator marketing badge from the database (`"Most Popular"` or `null`).
  - `is_active`: Boolean flag indicating if the plan is currently active or deactivated.
  - `subscribers`: Number of active subscribers currently enrolled in this plan.
  - `subscribers_percentage`: Share of total subscribers rounded to 1 decimal place.
  - `revenue`: Actual captured revenue generated by this plan in ₹ INR during the selected period.
  - `revenue_percentage`: Share of total period revenue rounded to 1 decimal place.

---

### 3.4 `GET /api/v1/admin/dashboard/recent-activity` — Recent Mobile Users & Subscribers

Powers the bottom-left feed widget showing latest member signups and paying subscriber conversions, with segmented filtering and standard pagination.

#### Business Logic & Rules

- **Strict Exclusion of Guests**: Anonymous guest sessions (`role = 'guest'`) are strictly excluded to prevent phantom accounts from polluting the feed. Only verified registered accounts (`role = 'subscriber'`) are returned.
- **Audience Segmentation (`filter`)**:
  - `"all"` _(default)_: Returns all registered accounts (both paying subscribers and free users), ordered by `joined_at DESC`.
  - `"subscribers"`: Returns only users with active paid subscriptions (`is_paid: true`), ordered by `subscribed_at DESC` so recent revenue conversions surface immediately.
  - `"users"`: Returns only non-paying registered users who have not purchased a plan (`is_paid: false`), ordered by `joined_at DESC`.
- **Nullable Email Handling**: For users who registered via Facebook without an email (phone-based registration) or denied email permissions, `email` is cleanly returned as `null`.

#### Headers

```http
Authorization: Bearer <admin_access_token>
```

#### Query Parameters

- `filter` _(string, optional, default: `"all"`)_: Classification filter (`"all"`, `"subscribers"`, `"users"`).
- `page` _(integer, optional, default: `1`, min: `1`)_: Page number for pagination.
- `limit` _(integer, optional, default: `5`, min: `1`, max: `20`)_: Number of records per page.

#### Response Envelope (`200 OK`)

Conforms strictly to the project-standard `PaginatedResponse[T]`:

```json
{
  "total": 45,
  "page": 1,
  "limit": 5,
  "total_pages": 9,
  "items": [
    {
      "id": 101,
      "name": "John Anderson",
      "email": "john.anderson@example.com",
      "avatar_url": "https://your-pull-zone.b-cdn.net/avatars/user_101.jpg",
      "plan_name": "Pro Yearly",
      "is_paid": true,
      "subscribed_at": "2026-09-09T11:20:00Z",
      "joined_at": "2026-07-15T14:32:00Z"
    },
    {
      "id": 102,
      "name": "Sarah Miller",
      "email": null,
      "avatar_url": null,
      "plan_name": null,
      "is_paid": false,
      "subscribed_at": null,
      "joined_at": "2026-09-08T09:15:00Z"
    },
    {
      "id": 103,
      "name": "Mike Johnson",
      "email": "mike.johnson@example.com",
      "avatar_url": null,
      "plan_name": "Standard Monthly",
      "is_paid": true,
      "subscribed_at": "2026-09-07T16:40:00Z",
      "joined_at": "2026-09-07T16:30:00Z"
    },
    {
      "id": 104,
      "name": "Emma Davis",
      "email": "emma.davis@example.com",
      "avatar_url": null,
      "plan_name": "Pro Yearly",
      "is_paid": true,
      "subscribed_at": "2026-09-06T12:10:00Z",
      "joined_at": "2026-08-01T10:00:00Z"
    },
    {
      "id": 105,
      "name": "Tom Wilson",
      "email": "tom.wilson@example.com",
      "avatar_url": null,
      "plan_name": null,
      "is_paid": false,
      "subscribed_at": null,
      "joined_at": "2026-09-05T14:00:00Z"
    }
  ]
}
```

#### Field Definitions

- `total`: Total matching records for the selected `filter`.
- `page`, `limit`, `total_pages`: Standard pagination controls.
- `items`: List of user records:
  - `id`: Database ID of the user.
  - `name`: User display name.
  - `email`: User email address, or `null` if registered via phone or permission was withheld.
  - `avatar_url`: CDN profile image URL, or `null`.
  - `plan_name`: Active subscription tier name, or `null` if non-paying user.
  - `is_paid`: Boolean flag indicating whether the user currently holds an active paid membership.
  - `subscribed_at`: ISO timestamp of when the user subscribed to their current active plan, or `null`.
  - `joined_at`: ISO timestamp of account creation.

---

### 3.5 Top Performing Content Feed — Reusing Existing `GET /api/v1/admin/videos`

To maintain clean architecture and prevent redundant database queries, the dashboard's **Top Performing Content** widget directly reuses the existing video management API implemented in `app/routes/admin/video_routes.py`.

#### Endpoint

```http
GET /api/v1/admin/videos?status=published&sort=views&limit=5
```

#### Headers

```http
Authorization: Bearer <admin_access_token>
```

#### Query Parameters for Dashboard Widget

- `status` _(string, optional, default: `"published"`)_: Filters only public, active content.
- `sort` _(string, optional, default: `"views"`)_: Sort order (`"views"` for highest audience reach, or `"newest"`, `"oldest"`, `"title"`).
- `page` _(integer, optional, default: `1`, min: `1`)_: Page number.
- `limit` _(integer, optional, default: `5`, min: `1`, max: `20`)_: Number of top videos to display.

#### Response Envelope (`200 OK`)

Returns standard `PaginatedResponse[VideoListItemResponse]`:

```json
{
  "total": 45,
  "page": 1,
  "limit": 5,
  "total_pages": 9,
  "items": [
    {
      "id": 12,
      "title": "Complete React Tutorial 2024",
      "category": "Development",
      "status": "published",
      "encode_progress": 100,
      "is_playable": true,
      "views": 124000,
      "likes": 8420,
      "duration": "14:20",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/thumbnails/video_12.jpg",
      "published_at": "2026-06-15T10:00:00Z",
      "scheduled_at": null,
      "created_at": "2026-06-15T09:00:00Z"
    },
    {
      "id": 15,
      "title": "Advanced JavaScript Patterns",
      "category": "Development",
      "status": "published",
      "encode_progress": 100,
      "is_playable": true,
      "views": 98000,
      "likes": 6150,
      "duration": "22:15",
      "main_thumbnail_url": "https://your-pull-zone.b-cdn.net/assets/thumbnails/video_15.jpg",
      "published_at": "2026-07-02T14:30:00Z",
      "scheduled_at": null,
      "created_at": "2026-07-02T14:00:00Z"
    }
  ]
}
```

> **Zero Redundancy**: The existing endpoint already executes an indexed query over `(user_id, views)` and includes CDN thumbnail URLs, video duration, and engagement counts. No separate `/dashboard/top-content` route is required.

---
