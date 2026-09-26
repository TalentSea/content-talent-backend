# Mobile Studio Branding API Specification

This document details the public API endpoint for Mobile Application subscribers and guests to fetch white-label studio branding attributes, logos, and cover banner assets upon mobile app initialization and splash screen loading.

---

## 1. Overview & Access Control

* **Base Endpoint**: `GET /api/v1/mobile/branding`
* **Authentication**: **Unauthenticated / Public**. No authorization token is required, allowing the mobile app to fetch branding assets immediately on cold-boot before login.
* **Multi-Tenant Isolation**: The client must provide the `X-Tenant-Id` HTTP header to specify which studio's branding to retrieve. The backend fetches the matching `Branding` record (`Tenant.id == X-Tenant-Id`).
* **Caching Strategy**: HTTP Header `Cache-Control: public, max-age=3600` is returned to enable local mobile client caching for fast cold-boot times (< 50ms).
* **Complete Initial Configuration**: Since tenant identity (`studio_name`, `tagline`, `description`) and default `theme` colors are fully configured upon tenant creation, mobile applications always receive complete brand text and color tokens on initial launch (only `logo_url` and `banner_url` remain `null` until uploaded).

---

## 2. API Endpoint Specification

### `GET /api/v1/mobile/branding`

#### Response Envelope (`200 OK`) — Configured Studio

```json
{
  "studio_name": "TechNics Training Studio",
  "tagline": "Master Modern Software Engineering & Cloud Architecture",
  "description": "Learn backend clean architecture, OTT video streaming systems, and cloud infrastructure with hands-on projects.",
  "banner_url": "https://talentsea77999.b-cdn.net/assets/branding/banner_1_1787293643.jpg",
  "logo_url": "https://talentsea77999.b-cdn.net/assets/branding/logo_1_1787293643.jpg",
  "theme": {
    "primaryColor": "#E50914",
    "secondaryColor": "#5865F2",
    "activeStateColor": "#5865F2",
    "mainBackgroundColor": "#000000",
    "cardBackgroundColor": "#12121A",
    "primaryTextColor": "#FFFFFF",
    "secondaryTextColor": "#9CA3AF",
    "mutedTextColor": "#6B7280",
    "buttonTextColor": "#FFFFFF"
  },
  "updated_at": "2026-08-21T14:30:00Z"
}
```

#### Response Envelope (`200 OK`) — Newly Provisioned Studio (Pre-Asset Upload)

When a new tenant studio is provisioned by Platform Super Admins, its brand identity (`studio_name`, `tagline`, `description`) and default `theme` colors are completely configured immediately. The only fields that initially return `null` are `banner_url` and `logo_url` until the creator studio admin uploads them via the Admin Portal:

```json
{
  "studio_name": "TechNics Training Studio",
  "tagline": "Master Modern Software Engineering & Cloud Architecture",
  "description": "Learn backend clean architecture, OTT video streaming systems, and cloud infrastructure with hands-on projects.",
  "banner_url": null,
  "logo_url": null,
  "theme": {
    "primaryColor": "#E50914",
    "secondaryColor": "#5865F2",
    "activeStateColor": "#5865F2",
    "mainBackgroundColor": "#000000",
    "cardBackgroundColor": "#12121A",
    "primaryTextColor": "#FFFFFF",
    "secondaryTextColor": "#9CA3AF",
    "mutedTextColor": "#6B7280",
    "buttonTextColor": "#FFFFFF"
  },
  "updated_at": "2026-08-21T14:30:00Z"
}
```



