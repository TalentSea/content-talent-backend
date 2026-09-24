# Mobile Application — Categories API Specification

## 1. System Architecture & Security Standards

### Authentication & Multi-Tenant Isolation Standard

All mobile requests pass an authenticated JWT session header:

```http
Authorization: Bearer <subscriber_access_token>
```

The FastAPI backend decodes the token in memory (< 1ms) to extract `current_subscriber["tenant_id"]`. The category feed is automatically filtered by `tenant_id` to guarantee 100% multi-tenant creator isolation.

### Standard HTTP Error Responses

#### 1. `500 Internal Server Error` — Database Error

```json
{
  "detail": "Internal server error occurred while retrieving mobile category feed"
}
```

---

## 📱 Mobile Categories Endpoints

### 1. `GET /api/v1/mobile/categories` — Get Mobile Category Filter Feed

Retrieves the list of active categories sorted by creator display order (`display_order` ascending) to render horizontal filter chips (`"All"`, `"Programming 💻"`, `"Design 🎨"`) on the mobile app home screen and explore tabs.

> [!NOTE]
> **Scope:** Category filter chips strictly apply to standard 16:9 catalog videos (`GET /api/v1/mobile/videos`). Vertical short videos (`GET /api/v1/mobile/videos/shorts`) have no category (`category: null`) and are not filtered by category chips.

#### Request Headers

```http
Authorization: Bearer <subscriber_access_token>
```

#### Query Parameters

None.

#### Internal Backend Workflow

1. Extracts `tenant_id` from `current_subscriber` JWT session token context.
2. Queries `Category` table filtering by `Category.tenant == tenant_id`.
3. Orders items by `Category.display_order.asc()`.
4. Maps lightweight DTO response (`id`, `name`, `slug`, `description`, `thumbnailUrl`, `color`).

#### Response Specification (`200 OK`)

```json
{
  "data": [
    {
      "id": 1,
      "name": "Tutorials",
      "slug": "tutorials",
      "description": "Comprehensive development walkthroughs and programming guides.",
      "thumbnailUrl": "https://talent-sea987.b-cdn.net/assets/categories/cat_1_1726732800.webp",
      "color": "#3b82f6"
    },
    {
      "id": 2,
      "name": "Design",
      "slug": "design",
      "description": "Creative design systems, UI/UX paradigms, and digital illustrations.",
      "thumbnailUrl": "https://talent-sea987.b-cdn.net/assets/categories/cat_2_1726732800.webp",
      "color": "#ec4899"
    }
  ]
}
```
