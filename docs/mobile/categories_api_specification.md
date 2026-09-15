# Mobile Application — Categories API Specification

## 1. System Architecture & Security Standards

### Authentication & Multi-Tenant Isolation Standard
All mobile requests pass an authenticated JWT session header:
```http
Authorization: Bearer <subscriber_access_token>
```
The FastAPI backend decodes the token in memory (< 1ms) to extract `current_subscriber["creator_id"]`. The category feed is automatically filtered by `creator_id` to guarantee 100% multi-tenant creator isolation.

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

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
```

#### Query Parameters
None.

#### Internal Backend Workflow
1. Extracts `creator_id` from `current_subscriber` JWT session token context.
2. Queries `Category` table filtering by `Category.user == creator_id`.
3. Orders items by `Category.display_order.asc()`.
4. Maps lightweight DTO response (`id`, `name`, `slug`, `icon`, `color`).

#### Response Specification (`200 OK`)
```json
{
  "items": [
    {
      "id": 1,
      "name": "Tutorials",
      "slug": "tutorials",
      "icon": "📚",
      "color": "#3b82f6"
    },
    {
      "id": 2,
      "name": "Design",
      "slug": "design",
      "icon": "🎨",
      "color": "#ec4899"
    }
  ]
}
```
