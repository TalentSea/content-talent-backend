# Mobile Featured Videos API Specification

This document details the RESTful API endpoint for Mobile Application subscribers and guests to fetch white-label creator featured videos for display on the home screen hero carousel.

---

## 1. Overview & Access Control

* **Base Endpoint**: `GET /api/v1/mobile/featured-videos`
* **Authentication**: **Subscriber Protected** (`Authorization: Bearer <subscriber_access_token>`).
* **Multi-Tenant Isolation**: The backend extracts `current_subscriber["creator_id"]` from the JWT token and fetches matching `FeaturedVideo` records (`FeaturedVideo.creator == creator_id`), ordered by `position` ascending.
* **Unconfigured Fallback**: If creator featured videos have not been configured in the database, returns HTTP `200 OK` with an empty array `[]` to enable smooth mobile home screen rendering without crashing.

---

## 2. API Endpoint Specification

### `GET /api/v1/mobile/featured-videos`

Retrieves creator featured videos ordered by display position for hero carousel rendering.

#### Headers
```http
Authorization: Bearer <subscriber_access_token>
```

#### Response Envelope (`200 OK`) — Configured Carousel

```json
[
  {
    "id": 45,
    "position": 1,
    "title": "Introduction to Clean Architecture in FastAPI",
    "category": "Backend Development",
    "main_thumbnail_url": "https://talentsea77999.b-cdn.net/thumbnails/v45_slot0.jpg",
    "duration": "14:20",
    "views": 1420,
    "likes": 88,
    "is_liked": false,
    "is_saved": true,
    "created_at": "2026-08-20T10:00:00Z"
  },
  {
    "id": 48,
    "position": 2,
    "title": "Mastering Bunny Stream & TUS Uploads",
    "category": "Video Engineering",
    "main_thumbnail_url": "https://talentsea77999.b-cdn.net/thumbnails/v48_slot0.jpg",
    "duration": "22:15",
    "views": 950,
    "likes": 64,
    "is_liked": true,
    "is_saved": false,
    "created_at": "2026-08-21T12:30:00Z"
  }
]
```

#### Response Envelope (`200 OK`) — Unconfigured Carousel Fallback

```json
[]
```
