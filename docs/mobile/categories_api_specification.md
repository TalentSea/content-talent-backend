# Mobile Application — Categories API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
The Mobile Categories API is publicly accessible by both **Guest users** (unauthenticated) and **Subscribers** (authenticated). 
If an incoming request includes an optional Bearer access token:
```http
Authorization: Bearer <subscriber_access_token>
```
The backend extracts caller context using `get_optional_subscriber`.

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
Authorization: Bearer <subscriber_access_token>  (Optional)
```

#### Query Parameters
None.

#### Internal Backend Workflow
1. Queries `Category` table for all records owned by the active creator.
2. Orders items by `Category.display_order.asc()`.
3. Maps lightweight DTO response (`id`, `name`, `slug`, `icon`, `color`).

#### Response Specification (`200 OK`)
```json
{
  "data": [
    {
      "id": 1,
      "name": "Programming",
      "slug": "programming",
      "icon": "💻",
      "color": "#3b82f6"
    },
    {
      "id": 2,
      "name": "Design & UI/UX",
      "slug": "design-ui-ux",
      "icon": "🎨",
      "color": "#ec4899"
    },
    {
      "id": 3,
      "name": "Mobile Development",
      "slug": "mobile-development",
      "icon": "📱",
      "color": "#10b981"
    }
  ]
}
```

---

## 🔗 Integration with Mobile Video API

The Mobile Categories API works in direct synergy with the **Mobile Video Feed API** (`GET /api/v1/mobile/videos`):

### 1. Step 1 — Render Category Filter Chips
The mobile app calls `GET /api/v1/mobile/categories` on launch to populate horizontal filter chips on the home screen:
* **"All"** (Default, `category = null`)
* **"Programming"** (`slug = "programming"`)
* **"Design & UI/UX"** (`slug = "design-ui-ux"`)
* **"Mobile Development"** (`slug = "mobile-development"`)

### 2. Step 2 — Filter Video Catalog by Category Slug
When the subscriber taps a filter chip (e.g. `"Design & UI/UX"`), the mobile app passes the category `slug` directly into the `category` query parameter of the Mobile Video Feed API:

```http
GET /api/v1/mobile/videos?category=design-ui-ux&page=1&limit=20
```

### 3. Step 3 — Backend SQL Query Execution
The backend `MobileVideoRepository` executes a filtered Peewee query:
```sql
SELECT * FROM videos 
WHERE status = 'published' 
  AND transcoding_status = 'READY' 
  AND LOWER(category) = 'design-ui-ux'
ORDER BY published_at DESC 
LIMIT 20 OFFSET 0;
```

Returning a paginated feed of published & ready video items assigned to that category along with personalized watch progress!
