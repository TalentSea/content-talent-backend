# Creator OTT Platform — API Documentation

**Base URL:** `https://api.yourplatform.com`  
**Version:** `v1`  
**Auth:** All endpoints (except `/auth/*`) require `Authorization: Bearer <access_token>` header.  
**Content-Type:** `application/json` (unless noted as `multipart/form-data`)

---

## Table of Contents

1. [Auth](#1-auth)
2. [Dashboard](#2-dashboard)
3. [Content Management — Videos](#3-content-management--videos)
4. [Content Management — Playlists](#4-content-management--playlists)
5. [Subscribers](#5-subscribers)
6. [Subscription Plans](#6-subscription-plans)
7. [Analytics](#7-analytics)
8. [Revenue](#8-revenue)
9. [Community — Announcements](#9-community--announcements)
10. [Community — Comments](#10-community--comments)
11. [Branding](#11-branding)
12. [Categories](#12-categories)
13. [Settings](#13-settings)
14. [Profile](#14-profile)

---

## 1. Auth

### POST `api/v1/auth/login`
Login with email and password.

**Request Body**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response `200`**
```json
{
  "accessToken": "string",
  "refreshToken": "string",
  "expiresIn": 3600,
  "user": {
    "id": "string",
    "name": "string",
    "email": "string",
    "avatar": "string | null"
  }
}
```

---

### POST `api/v1/auth/logout`
Invalidate the current session.

**Request Body**
```json
{
  "refreshToken": "string"
}
```

**Response `200`**
```json
{
  "message": "Logged out successfully"
}
```

---

### POST `api/v1/auth/refresh`
Get a new access token using a refresh token.

**Request Body**
```json
{
  "refreshToken": "string"
}
```

**Response `200`**
```json
{
  "accessToken": "string",
  "expiresIn": 3600
}
```

---

### POST `api/v1/auth/forgot-password`
Send a password reset email.

**Request Body**
```json
{
  "email": "string"
}
```

**Response `200`**
```json
{
  "message": "Password reset email sent"
}
```

---

### POST `api/v1/auth/reset-password`
Reset password using the token from email.

**Request Body**
```json
{
  "token": "string",
  "newPassword": "string",
  "confirmPassword": "string"
}
```

**Response `200`**
```json
{
  "message": "Password reset successfully"
}
```

---

## 2. Dashboard

### GET `api/v1/stats/overview`
Get top-level platform statistics for the dashboard.

**Query Parameters** — none

**Response `200`**
```json
{
  "totalUsers": 125430,
  "totalSubscribers": 14567,
  "subscriberGrowthRate": 12.5,
  "totalContent": 342,
  "monthlyRevenue": 48920.50,
  "totalViews": 2400000
}
```

---

### GET `api/v1/revenue/chart`
Get monthly revenue and subscriber growth for the composed chart.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | `3m`, `6m`, `12m` — default `6m` |

**Response `200`**
```json
{
  "data": [
    {
      "month": "Jan",
      "revenue": 38500,
      "subscribers": 10200
    }
  ]
}
```

---

### GET `api/v1/analytics/device-distribution`
Get device-type breakdown of platform users.

**Query Parameters** — none

**Response `200`**
```json
{
  "data": [
    { "device": "Android", "percentage": 34, "users": 42680 },
    { "device": "iOS", "percentage": 28, "users": 35120 },
    { "device": "Windows", "percentage": 18, "users": 22577 },
    { "device": "macOS", "percentage": 12, "users": 15052 },
    { "device": "Smart TV", "percentage": 5, "users": 6271 },
    { "device": "Other", "percentage": 3, "users": 3763 }
  ]
}
```

---

### GET `api/v1/subscribers/recent`
Get the most recently joined subscribers.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | `number` | No | Number of results — default `5` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "email": "string",
      "plan": "Basic | Premium | Annual Basic",
      "joinedAt": "2024-06-20T10:30:00Z",
      "avatar": "string | null"
    }
  ]
}
```

---

### GET `api/v1/content/top-performing`
Get top videos sorted by a given metric.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `sort` | `string` | No | `views`, `watchTime`, `engagement` — default `views` |
| `limit` | `number` | No | Default `4` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "thumbnail": "string",
      "category": "string",
      "views": 124500,
      "duration": "18:42",
      "publishedAt": "2024-06-01T00:00:00Z"
    }
  ]
}
```

---

## 3. Content Management — Videos

### GET `api/v1/videos`
Get all videos with optional filters.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | `string` | No | `published`, `draft`, `scheduled` |
| `category` | `string` | No | Category ID |
| `search` | `string` | No | Search by title |
| `sort` | `string` | No | `newest`, `oldest`, `views`, `title` |
| `dateFrom` | `string` | No | ISO date — `2024-01-01` |
| `dateTo` | `string` | No | ISO date — `2024-06-30` |
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `20` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "thumbnail": "string",
      "category": { "id": "string", "name": "string" },
      "status": "published | draft | scheduled",
      "views": 12400,
      "duration": "18:42",
      "tags": ["string"],
      "publishedAt": "2024-06-01T00:00:00Z",
      "scheduledAt": "2024-07-01T09:00:00Z | null",
      "createdAt": "2024-05-20T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 342,
    "page": 1,
    "limit": 20,
    "totalPages": 18
  }
}
```

---

### GET `api/v1/videos/:id`
Get a single video's full details.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Video ID |

**Response `200`**
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "thumbnails": ["string", "string", "string"],
  "category": { "id": "string", "name": "string" },
  "status": "published | draft | scheduled",
  "views": 12400,
  "duration": "18:42",
  "comments": 234,
  "tags": ["string"],
  "playlists": [{ "id": "string", "title": "string" }],
  "publishedAt": "2024-06-01T00:00:00Z",
  "scheduledAt": "2024-07-01T09:00:00Z | null",
  "createdAt": "2024-05-20T00:00:00Z"
}
```

---

### POST `api/v1/videos/upload`
Upload a new video.

**Content-Type:** `multipart/form-data`

**Request Fields**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | `File` | Yes | Video file |
| `title` | `string` | Yes | Video title |
| `category` | `string` | Yes | Category ID |
| `description` | `string` | No | Video description |
| `tags` | `string[]` | No | Array of tag strings |
| `thumbnails` | `File[]` | No | Up to 3 thumbnail images |
| `playlistIds` | `string[]` | No | Playlist IDs to add to |
| `status` | `string` | No | `draft` (default) or `published` |

**Response `201`**
```json
{
  "id": "string",
  "title": "string",
  "status": "draft",
  "uploadProgress": 100,
  "createdAt": "2024-06-20T10:30:00Z"
}
```

---

### PUT `api/v1/videos/:id`
Edit an existing video's details.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Video ID |

**Request Body**
```json
{
  "title": "string",
  "description": "string",
  "category": "string",
  "tags": ["string"],
  "thumbnails": ["string"],
  "playlistIds": ["string"]
}
```

**Response `200`**
```json
{
  "id": "string",
  "title": "string",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### DELETE `api/v1/videos/:id`
Delete a video permanently.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Video ID |

**Response `200`**
```json
{
  "message": "Video deleted successfully"
}
```

---

### POST `api/v1/videos/:id/publish`
Publish a video immediately.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Video ID |

**Request Body** — none

**Response `200`**
```json
{
  "id": "string",
  "status": "published",
  "publishedAt": "2024-06-20T10:30:00Z"
}
```

---

### POST `api/v1/videos/:id/schedule`
Schedule a video for future publishing.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Video ID |

**Request Body**
```json
{
  "date": "2024-07-01",
  "time": "09:00",
  "timezone": "America/Los_Angeles"
}
```

**Response `200`**
```json
{
  "id": "string",
  "status": "scheduled",
  "scheduledAt": "2024-07-01T16:00:00Z"
}
```

---

## 4. Content Management — Playlists

### GET `api/v1/playlists`
Get all playlists.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `search` | `string` | No | Search by title |
| `sort` | `string` | No | `newest`, `oldest`, `title`, `videoCount` |
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `20` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "thumbnail": "string",
      "videoCount": 12,
      "createdAt": "2024-05-01T00:00:00Z",
      "updatedAt": "2024-06-10T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 24,
    "page": 1,
    "limit": 20,
    "totalPages": 2
  }
}
```

---

### GET `api/v1/playlists/:id`
Get a single playlist's details.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Playlist ID |

**Response `200`**
```json
{
  "id": "string",
  "title": "string",
  "description": "string",
  "thumbnail": "string",
  "videoCount": 12,
  "createdAt": "2024-05-01T00:00:00Z"
}
```

---

### POST `api/v1/playlists`
Create a new playlist.

**Content-Type:** `multipart/form-data`

**Request Fields**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | Yes | Playlist title |
| `description` | `string` | No | Playlist description |
| `thumbnail` | `File` | No | Thumbnail image |
| `videoIds` | `string[]` | No | Initial video IDs to add |

**Response `201`**
```json
{
  "id": "string",
  "title": "string",
  "videoCount": 0,
  "createdAt": "2024-06-20T10:30:00Z"
}
```

---

### PUT `api/v1/playlists/:id`
Edit a playlist's metadata.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Playlist ID |

**Content-Type:** `multipart/form-data`

**Request Fields**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | `string` | No | Updated title |
| `description` | `string` | No | Updated description |
| `thumbnail` | `File` | No | New thumbnail image |

**Response `200`**
```json
{
  "id": "string",
  "title": "string",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### DELETE `api/v1/playlists/:id`
Delete a playlist (does not delete the videos inside it).

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Playlist ID |

**Response `200`**
```json
{
  "message": "Playlist deleted successfully"
}
```

---

### GET `api/v1/playlists/:id/videos`
Get all videos inside a specific playlist.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Playlist ID |

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `search` | `string` | No | Search by title |
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `20` |

**Response `200`**
```json
{
  "playlistId": "string",
  "playlistTitle": "string",
  "data": [
    {
      "id": "string",
      "title": "string",
      "thumbnail": "string",
      "duration": "18:42",
      "views": 12400,
      "order": 1,
      "addedAt": "2024-06-10T00:00:00Z"
    }
  ],
  "pagination": {
    "total": 12,
    "page": 1,
    "limit": 20,
    "totalPages": 1
  }
}
```

---

### POST `api/v1/playlists/:id/videos`
Add videos to a playlist.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Playlist ID |

**Request Body**
```json
{
  "videoIds": ["string", "string"]
}
```

**Response `200`**
```json
{
  "message": "Videos added successfully",
  "videoCount": 14
}
```

---

### DELETE `api/v1/playlists/:id/videos/:videoId`
Remove a single video from a playlist.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Playlist ID |
| `videoId` | `string` | Video ID |

**Response `200`**
```json
{
  "message": "Video removed from playlist",
  "videoCount": 11
}
```

---

### DELETE `api/v1/playlists/:id/videos`
Bulk remove multiple videos from a playlist.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Playlist ID |

**Request Body**
```json
{
  "videoIds": ["string", "string"]
}
```

**Response `200`**
```json
{
  "message": "Videos removed successfully",
  "videoCount": 10
}
```

---

## 5. Subscribers

### GET `api/v1/subscribers/stats`
Get aggregate subscriber statistics.

**Query Parameters** — none

**Response `200`**
```json
{
  "totalSubscribers": 14567,
  "growthRate": 12.5,
  "avgRevenuePerUser": 24.80,
  "churnRate": 2.1
}
```

---

### GET `api/v1/subscribers/plan-distribution`
Get subscriber count broken down by plan (for pie chart).

**Query Parameters** — none

**Response `200`**
```json
{
  "data": [
    { "plan": "Premium", "count": 8234, "percentage": 56.5 },
    { "plan": "Basic", "count": 4309, "percentage": 29.6 },
    { "plan": "Annual Basic", "count": 1245, "percentage": 8.5 },
    { "plan": "Trial", "count": 779, "percentage": 5.4 }
  ]
}
```

---

### GET `api/v1/subscribers`
Get a paginated, filterable list of subscribers.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `plan` | `string` | No | `Basic`, `Premium`, `Annual Basic`, `Trial` |
| `status` | `string` | No | `active`, `suspended`, `cancelled` |
| `joinDateFrom` | `string` | No | ISO date — `2024-01-01` |
| `joinDateTo` | `string` | No | ISO date — `2024-06-30` |
| `search` | `string` | No | Search by name or email |
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `20` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "name": "string",
      "email": "string",
      "plan": "Premium",
      "status": "active",
      "revenue": 29.99,
      "joinedAt": "2024-03-15T00:00:00Z",
      "avatar": "string | null"
    }
  ],
  "pagination": {
    "total": 14567,
    "page": 1,
    "limit": 20,
    "totalPages": 729
  }
}
```

---

### GET `api/v1/subscribers/:id`
Get a single subscriber's profile.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Subscriber ID |

**Response `200`**
```json
{
  "id": "string",
  "name": "string",
  "email": "string",
  "plan": "Premium",
  "status": "active",
  "totalRevenue": 359.88,
  "joinedAt": "2024-03-15T00:00:00Z",
  "lastActiveAt": "2024-06-19T14:22:00Z",
  "avatar": "string | null"
}
```

---

### PUT `api/v1/subscribers/:id/plan`
Change a subscriber's plan.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Subscriber ID |

**Request Body**
```json
{
  "plan": "Basic | Premium | Annual Basic"
}
```

**Response `200`**
```json
{
  "id": "string",
  "plan": "Basic",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### POST `api/v1/subscribers/:id/email`
Send a direct email to a subscriber.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Subscriber ID |

**Request Body**
```json
{
  "subject": "string",
  "body": "string"
}
```

**Response `200`**
```json
{
  "message": "Email sent successfully"
}
```

---

### PUT `api/v1/subscribers/:id/suspend`
Suspend a subscriber's account.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Subscriber ID |

**Request Body**
```json
{
  "reason": "string"
}
```

**Response `200`**
```json
{
  "id": "string",
  "status": "suspended",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### PUT `api/v1/subscribers/:id/reinstate`
Reinstate a suspended subscriber.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Subscriber ID |

**Request Body** — none

**Response `200`**
```json
{
  "id": "string",
  "status": "active",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

## 6. Subscription Plans

### GET `api/v1/plans`
Get all subscription plans.

**Query Parameters** — none

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "name": "Premium",
      "price": 29.99,
      "period": "month",
      "description": "string",
      "features": ["string"],
      "active": true,
      "popular": true,
      "subscribers": 8234,
      "monthlyRevenue": 246898.00
    }
  ]
}
```

---

### GET `api/v1/plans/:id`
Get a single plan's full details.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Plan ID |

**Response `200`**
```json
{
  "id": "string",
  "name": "string",
  "price": 29.99,
  "period": "month",
  "description": "string",
  "features": ["string"],
  "active": true,
  "popular": false,
  "subscribers": 8234,
  "monthlyRevenue": 246898.00,
  "createdAt": "2024-01-01T00:00:00Z"
}
```

---

### POST `api/v1/plans`
Create a new subscription plan.

**Request Body**
```json
{
  "name": "string",
  "price": 19.99,
  "period": "month | year",
  "description": "string",
  "features": ["string"],
  "active": true
}
```

**Response `201`**
```json
{
  "id": "string",
  "name": "string",
  "createdAt": "2024-06-20T10:30:00Z"
}
```

---

### PUT `api/v1/plans/:id`
Edit an existing plan.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Plan ID |

**Request Body**
```json
{
  "name": "string",
  "price": 19.99,
  "period": "month | year",
  "description": "string",
  "features": ["string"],
  "active": true
}
```

**Response `200`**
```json
{
  "id": "string",
  "name": "string",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### DELETE `api/v1/plans/:id`
Delete a subscription plan.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Plan ID |

**Response `200`**
```json
{
  "message": "Plan deleted successfully"
}
```

---

### PATCH `api/v1/plans/:id/toggle`
Toggle a plan's active/inactive status.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Plan ID |

**Request Body** — none

**Response `200`**
```json
{
  "id": "string",
  "active": false,
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

## 7. Analytics

### GET `api/v1/analytics/metrics`
Get headline performance metrics.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | `7d`, `30d`, `90d`, `365d` — default `30d` |

**Response `200`**
```json
{
  "totalViews": 2400000,
  "viewsChange": 18.2,
  "watchTimeHours": 1200000,
  "watchTimeChange": 12.5,
  "engagementRate": 68.3,
  "engagementChange": -2.3,
  "avgViewDuration": "28:42",
  "avgViewDurationChange": 5.1
}
```

---

### GET `api/v1/analytics/views-watchtime`
Get time-series views and watch time data for the area chart.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | `7d`, `30d`, `90d`, `365d` — default `30d` |

**Response `200`**
```json
{
  "data": [
    {
      "date": "Jun 1",
      "views": 12400,
      "watchTime": 8200
    }
  ]
}
```

---

### GET `api/v1/analytics/engagement-by-category`
Get engagement breakdown per content category.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | `7d`, `30d`, `90d` — default `30d` |

**Response `200`**
```json
{
  "data": [
    {
      "category": "Programming",
      "engagementRate": 92,
      "avgDuration": 48
    }
  ]
}
```

---

### GET `api/v1/analytics/device-distribution`
Get device type breakdown for the Analytics page.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | Default `30d` |

**Response `200`**
```json
{
  "data": [
    { "device": "Mobile", "users": 6543, "percentage": 52 },
    { "device": "Desktop", "users": 4231, "percentage": 34 },
    { "device": "Tablet", "users": 1769, "percentage": 14 }
  ]
}
```

---

### GET `api/v1/analytics/geographic`
Get top countries by user count.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `limit` | `number` | No | Default `5` |
| `period` | `string` | No | Default `30d` |

**Response `200`**
```json
{
  "data": [
    {
      "country": "United States",
      "countryCode": "US",
      "flag": "🇺🇸",
      "users": 4521
    }
  ]
}
```

---

### GET `api/v1/analytics/export`
Download an analytics report.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | `7d`, `30d`, `90d`, `365d` |
| `format` | `string` | No | `csv` (default) or `pdf` |

**Response `200`**  
Binary file download (`text/csv` or `application/pdf`).

---

## 8. Revenue

### GET `api/v1/revenue/stats`
Get top-level revenue statistics.

**Query Parameters** — none

**Response `200`**
```json
{
  "totalRevenue": 1248920.50,
  "thisMonthRevenue": 48920.50,
  "monthlyChange": 8.3,
  "activeSubscriptions": 14567,
  "avgRevenuePerUser": 24.80
}
```

---

### GET `api/v1/revenue/monthly`
Get monthly subscription revenue for bar chart.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | `3m`, `6m`, `12m` — default `6m` |

**Response `200`**
```json
{
  "data": [
    {
      "month": "Jan",
      "revenue": 38500
    }
  ]
}
```

---

### GET `api/v1/revenue/plan-breakdown`
Get revenue and subscriber count per plan type.

**Query Parameters** — none

**Response `200`**
```json
{
  "data": [
    {
      "plan": "Premium",
      "subscribers": 8234,
      "revenue": 246898.00,
      "percentage": 59.8
    }
  ]
}
```

---

### GET `api/v1/revenue/transactions`
Get paginated recent transactions.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `20` |
| `status` | `string` | No | `completed`, `refunded`, `failed` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "txn_abc123",
      "customer": "John Doe",
      "email": "john@example.com",
      "plan": "Premium",
      "amount": 29.99,
      "status": "completed",
      "date": "2024-06-20T10:30:00Z"
    }
  ],
  "pagination": {
    "total": 4820,
    "page": 1,
    "limit": 20,
    "totalPages": 241
  }
}
```

---

### GET `api/v1/revenue/payout/next`
Get the next scheduled payout details.

**Query Parameters** — none

**Response `200`**
```json
{
  "amount": 41582.30,
  "expectedDate": "2024-07-01T00:00:00Z",
  "currency": "USD"
}
```

---

### GET `api/v1/revenue/payout/history`
Get historical payout records.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `10` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "amount": 38920.50,
      "currency": "USD",
      "status": "paid",
      "paidAt": "2024-06-01T00:00:00Z"
    }
  ]
}
```

---

### GET `api/v1/revenue/export`
Download a revenue report.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | `string` | No | `3m`, `6m`, `12m` |
| `format` | `string` | No | `csv` (default) or `pdf` |

**Response `200`**  
Binary file download (`text/csv` or `application/pdf`).

---

## 9. Community — Announcements

### GET `api/v1/announcements`
Get all announcements.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `10` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "title": "string",
      "content": "string",
      "targetAudience": "all | premium | basic",
      "createdAt": "2024-06-15T09:00:00Z",
      "updatedAt": "2024-06-15T09:00:00Z"
    }
  ]
}
```

---

### POST `api/v1/announcements`
Create a new announcement.

**Request Body**
```json
{
  "title": "string",
  "content": "string",
  "targetAudience": "all | premium | basic"
}
```

**Response `201`**
```json
{
  "id": "string",
  "title": "string",
  "createdAt": "2024-06-20T10:30:00Z"
}
```

---

### PUT `api/v1/announcements/:id`
Edit an announcement.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Announcement ID |

**Request Body**
```json
{
  "title": "string",
  "content": "string",
  "targetAudience": "all | premium | basic"
}
```

**Response `200`**
```json
{
  "id": "string",
  "title": "string",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### DELETE `api/v1/announcements/:id`
Delete an announcement.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Announcement ID |

**Response `200`**
```json
{
  "message": "Announcement deleted successfully"
}
```

---

## 10. Community — Comments

### GET `api/v1/community/stats`
Get community engagement summary.

**Query Parameters** — none

**Response `200`**
```json
{
  "totalComments": 12450,
  "totalAnnouncements": 24,
  "engagementRate": 68.3,
  "pendingModeration": 18
}
```

---

### GET `api/v1/comments`
Get paginated, filtered comments.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `category` | `string` | No | Filter by content category ID |
| `videoId` | `string` | No | Filter by specific video ID |
| `date` | `string` | No | ISO date — filter by day |
| `minLikes` | `number` | No | Minimum number of likes |
| `search` | `string` | No | Search comment text |
| `sort` | `string` | No | `newest`, `oldest`, `mostLiked` |
| `page` | `number` | No | Default `1` |
| `limit` | `number` | No | Default `20` |

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "text": "string",
      "author": {
        "id": "string",
        "name": "string",
        "avatar": "string | null"
      },
      "videoId": "string",
      "videoTitle": "string",
      "likes": 42,
      "status": "approved | pending | removed",
      "createdAt": "2024-06-18T14:22:00Z",
      "replies": [
        {
          "id": "string",
          "text": "string",
          "author": { "id": "string", "name": "string" },
          "createdAt": "2024-06-18T15:00:00Z"
        }
      ]
    }
  ],
  "pagination": {
    "total": 12450,
    "page": 1,
    "limit": 20,
    "totalPages": 623
  }
}
```

---

### POST `api/v1/comments/:id/reply`
Reply to a comment.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Comment ID |

**Request Body**
```json
{
  "text": "string"
}
```

**Response `201`**
```json
{
  "id": "string",
  "text": "string",
  "createdAt": "2024-06-20T10:30:00Z"
}
```

---

### DELETE `api/v1/comments/:id`
Delete/remove a comment.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Comment ID |

**Response `200`**
```json
{
  "message": "Comment removed successfully"
}
```

---

### PUT `api/v1/comments/:id/approve`
Approve a pending comment.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Comment ID |

**Request Body** — none

**Response `200`**
```json
{
  "id": "string",
  "status": "approved",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

## 11. Branding

### GET `api/v1/branding`
Get current branding configuration.

**Query Parameters** — none

**Response `200`**
```json
{
  "appName": "string",
  "primaryColor": "#8b5cf6",
  "secondaryColor": "#3b82f6",
  "accentColor": "#ec4899",
  "logoUrl": "string | null",
  "faviconUrl": "string | null",
  "fontHeading": "Inter",
  "fontBody": "Inter",
  "updatedAt": "2024-06-10T00:00:00Z"
}
```

---

### PUT `api/v1/branding`
Save branding settings.

**Request Body**
```json
{
  "appName": "string",
  "primaryColor": "#8b5cf6",
  "secondaryColor": "#3b82f6",
  "accentColor": "#ec4899",
  "fontHeading": "string",
  "fontBody": "string"
}
```

**Response `200`**
```json
{
  "message": "Branding updated successfully",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### POST `api/v1/branding/logo`
Upload a logo image.

**Content-Type:** `multipart/form-data`

**Request Fields**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `logo` | `File` | Yes | Logo image (PNG/SVG, max 2MB) |
| `type` | `string` | No | `logo` (default) or `favicon` |

**Response `200`**
```json
{
  "logoUrl": "https://cdn.yourplatform.com/logos/abc123.png"
}
```

---

### POST `api/v1/branding/preview`
Generate a live app preview with current branding settings.

**Request Body**
```json
{
  "appName": "string",
  "primaryColor": "#8b5cf6",
  "secondaryColor": "#3b82f6",
  "logoUrl": "string | null"
}
```

**Response `200`**
```json
{
  "previewUrl": "https://cdn.yourplatform.com/previews/session_abc123.png",
  "expiresAt": "2024-06-20T11:00:00Z"
}
```

---

## 12. Categories

### GET `api/v1/categories`
Get all categories with content counts.

**Query Parameters** — none

**Response `200`**
```json
{
  "data": [
    {
      "id": "string",
      "name": "Programming",
      "description": "string",
      "icon": "💻",
      "color": "#3b82f6",
      "contentCount": 98,
      "order": 2,
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

---

### GET `api/v1/categories/:id`
Get a single category.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Category ID |

**Response `200`**
```json
{
  "id": "string",
  "name": "string",
  "description": "string",
  "icon": "string",
  "color": "string",
  "contentCount": 98,
  "order": 2
}
```

---

### POST `api/v1/categories`
Create a new category.

**Request Body**
```json
{
  "name": "string",
  "description": "string",
  "icon": "💻",
  "color": "#3b82f6"
}
```

**Response `201`**
```json
{
  "id": "string",
  "name": "string",
  "createdAt": "2024-06-20T10:30:00Z"
}
```

---

### PUT `api/v1/categories/:id`
Edit a category.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Category ID |

**Request Body**
```json
{
  "name": "string",
  "description": "string",
  "icon": "string",
  "color": "string"
}
```

**Response `200`**
```json
{
  "id": "string",
  "name": "string",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### DELETE `api/v1/categories/:id`
Delete a category.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `id` | `string` | Category ID |

**Response `200`**
```json
{
  "message": "Category deleted successfully"
}
```

---

### PUT `api/v1/categories/reorder`
Save drag-and-drop category order.

**Request Body**
```json
{
  "ids": ["cat_3", "cat_1", "cat_5", "cat_2", "cat_4", "cat_6"]
}
```

**Response `200`**
```json
{
  "message": "Category order updated"
}
```

---

## 13. Settings

### GET `api/v1/settings`
Get all settings for the logged-in creator.

**Query Parameters** — none

**Response `200`**
```json
{
  "profile": {
    "firstName": "string",
    "lastName": "string",
    "email": "string",
    "bio": "string",
    "website": "string",
    "phone": "string",
    "location": "string",
    "social": {
      "twitter": "string",
      "youtube": "string",
      "instagram": "string"
    }
  },
  "notifications": {
    "emailNewSubscribers": true,
    "emailComments": true,
    "emailRevenue": true,
    "emailPerformance": false,
    "pushMobile": true,
    "pushDesktop": false
  },
  "billing": {
    "bankAccount": "••••5678",
    "payoutSchedule": "monthly",
    "minimumPayout": 100
  },
  "preferences": {
    "language": "en",
    "timezone": "America/Los_Angeles",
    "currency": "USD"
  },
  "security": {
    "twoFactorEnabled": false,
    "activeSessions": 2
  }
}
```

---

### PUT `api/v1/settings/profile`
Update profile information.

**Request Body**
```json
{
  "firstName": "string",
  "lastName": "string",
  "email": "string",
  "bio": "string",
  "website": "string",
  "phone": "string",
  "location": "string",
  "social": {
    "twitter": "string",
    "youtube": "string",
    "instagram": "string"
  }
}
```

**Response `200`**
```json
{
  "message": "Profile updated successfully",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### PUT `api/v1/settings/notifications`
Update notification preferences.

**Request Body**
```json
{
  "emailNewSubscribers": true,
  "emailComments": true,
  "emailRevenue": true,
  "emailPerformance": false,
  "pushMobile": true,
  "pushDesktop": false
}
```

**Response `200`**
```json
{
  "message": "Notification preferences updated"
}
```

---

### PUT `api/v1/settings/security`
Update password.

**Request Body**
```json
{
  "currentPassword": "string",
  "newPassword": "string",
  "confirmPassword": "string"
}
```

**Response `200`**
```json
{
  "message": "Password updated successfully"
}
```

---

### POST `api/v1/settings/security/2fa/enable`
Enable two-factor authentication.

**Request Body** — none

**Response `200`**
```json
{
  "qrCodeUrl": "string",
  "secret": "string",
  "backupCodes": ["string", "string", "string"]
}
```

---

### POST `api/v1/settings/security/2fa/disable`
Disable two-factor authentication.

**Request Body**
```json
{
  "code": "123456"
}
```

**Response `200`**
```json
{
  "message": "2FA disabled successfully"
}
```

---

### DELETE `api/v1/settings/sessions/:sessionId`
Revoke a specific active session.

**Path Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `sessionId` | `string` | Session ID |

**Response `200`**
```json
{
  "message": "Session revoked"
}
```

---

### PUT `api/v1/settings/billing`
Update payout and billing settings.

**Request Body**
```json
{
  "bankAccount": "string",
  "payoutSchedule": "weekly | monthly",
  "minimumPayout": 100
}
```

**Response `200`**
```json
{
  "message": "Billing settings updated"
}
```

---

### PUT `api/v1/settings/preferences`
Update language, timezone and currency preferences.

**Request Body**
```json
{
  "language": "en | es | fr | de",
  "timezone": "America/Los_Angeles",
  "currency": "USD | EUR | GBP"
}
```

**Response `200`**
```json
{
  "message": "Preferences updated"
}
```

---

### GET `api/v1/settings/data/export`
Download a copy of the creator's data.

**Query Parameters** — none

**Response `200`**  
Binary file download (`application/zip`).

---

### POST `api/v1/settings/data/delete-request`
Submit a request for data deletion (GDPR).

**Request Body** — none

**Response `200`**
```json
{
  "message": "Data deletion request submitted. You will receive a confirmation email."
}
```

---

### POST `api/v1/settings/account/deactivate`
Temporarily deactivate the account.

**Request Body**
```json
{
  "password": "string",
  "reason": "string"
}
```

**Response `200`**
```json
{
  "message": "Account deactivated. You can reactivate at any time by logging in."
}
```

---

### DELETE `api/v1/settings/account`
Permanently delete the account and all associated data.

**Request Body**
```json
{
  "password": "string",
  "confirmText": "DELETE"
}
```

**Response `200`**
```json
{
  "message": "Account permanently deleted"
}
```

---

## 14. Profile

### GET `api/v1/profile`
Get the logged-in creator's profile.

**Query Parameters** — none

**Response `200`**
```json
{
  "id": "string",
  "firstName": "string",
  "lastName": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "bio": "string",
  "avatar": "string | null",
  "website": "string",
  "stats": {
    "totalSubscribers": 14567,
    "totalVideos": 342,
    "totalViews": 2400000,
    "totalRevenue": 1248920.50
  },
  "createdAt": "2023-01-15T00:00:00Z"
}
```

---

### PUT `api/v1/profile`
Update the creator's profile details.

**Request Body**
```json
{
  "firstName": "string",
  "lastName": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "bio": "string",
  "website": "string"
}
```

**Response `200`**
```json
{
  "message": "Profile updated successfully",
  "updatedAt": "2024-06-20T10:30:00Z"
}
```

---

### POST `api/v1/profile/photo`
Upload a profile photo.

**Content-Type:** `multipart/form-data`

**Request Fields**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `photo` | `File` | Yes | Image file (JPG/PNG, max 2MB) |

**Response `200`**
```json
{
  "avatarUrl": "https://cdn.yourplatform.com/avatars/abc123.jpg"
}
```

---

## Common Error Responses

All endpoints may return these standard error shapes:

**`400` Bad Request**
```json
{
  "error": "VALIDATION_ERROR",
  "message": "string",
  "details": [{ "field": "string", "message": "string" }]
}
```

**`401` Unauthorized**
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or expired token"
}
```

**`403` Forbidden**
```json
{
  "error": "FORBIDDEN",
  "message": "You do not have permission to perform this action"
}
```

**`404` Not Found**
```json
{
  "error": "NOT_FOUND",
  "message": "Resource not found"
}
```

**`500` Internal Server Error**
```json
{
  "error": "INTERNAL_ERROR",
  "message": "An unexpected error occurred"
}
```

---

*Total endpoints: 75 | Generated for Creator OTT Platform Admin Panel*
