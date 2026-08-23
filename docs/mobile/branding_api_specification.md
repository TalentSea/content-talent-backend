# Mobile Studio Branding API Specification

This document details the public API endpoint for Mobile Application subscribers and guests to fetch white-label studio branding attributes, logos, and cover banner assets upon mobile app initialization and splash screen loading.

---

## 1. Overview & Access Control

* **Base Endpoint**: `GET /api/v1/mobile/branding`
* **Authentication**: **Subscriber Protected** (`Authorization: Bearer <subscriber_access_token>`).
* **Multi-Tenant Isolation**: The backend extracts `current_subscriber["creator_id"]` from the JWT token and fetches the matching `Branding` record (`Branding.user == creator_id`).
* **Caching Strategy**: HTTP Header `Cache-Control: public, max-age=3600` is returned to enable local mobile client caching for fast cold-boot times (< 50ms).
* **Unconfigured Fallback**: If creator branding has not been configured in the database, returns HTTP `200 OK` with `null` fields to enable smooth mobile app cold-boot rendering.

---

## 2. API Endpoint Specification

### `GET /api/v1/mobile/branding`

#### Response Envelope (`200 OK`) — Configured Studio

```json
{
  "creator_name": "TechNics Training Studio",
  "tagline": "Master Modern Software Engineering & Cloud Architecture",
  "description": "Learn backend clean architecture, OTT video streaming systems, and cloud infrastructure with hands-on projects.",
  "banner_url": "https://talentsea77999.b-cdn.net/assets/branding/banner_1_1787293643.jpg",
  "logo_url": "https://talentsea77999.b-cdn.net/assets/branding/logo_1_1787293643.jpg",
  "updated_at": "2026-08-21T14:30:00Z"
}
```

#### Response Envelope (`200 OK`) — Unconfigured Fallback

```json
{
  "creator_name": null,
  "tagline": null,
  "description": null,
  "banner_url": null,
  "logo_url": null,
  "updated_at": null
}
```
