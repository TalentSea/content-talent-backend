# Creator Admin — Categories Management API Specification

## 1. System Architecture & Security Standards

### Authentication & Authorization Standard
All endpoints in this specification require a valid JWT Bearer access token passed in the HTTP request header:
```http
Authorization: Bearer <creator_access_token>
```
Identity and creator ownership are strictly derived from the validated JWT token (`get_current_admin`). Under no circumstances is `user_id` accepted as an HTTP query parameter or request body parameter, eliminating Insecure Direct Object Reference (IDOR) vulnerabilities.

### Standard HTTP Error Responses

All error responses across all endpoints follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid Request Payload
```json
{
  "detail": "Category name already exists for this creator account."
}
```

#### 2. `401 Unauthorized` — Missing or Expired JWT Token
```json
{
  "detail": "Could not validate credentials"
}
```

#### 3. `404 Not Found` — Resource Not Found or Forbidden Ownership
```json
{
  "detail": "Category with ID 5 not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Internal Failure
```json
{
  "detail": "Internal server error occurred while processing category operation"
}
```

---

## 📁 Database Schema Specification (`categories` Table)

```sql
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    description TEXT NULL,
    icon VARCHAR(50) NULL DEFAULT '📁',
    color VARCHAR(30) NULL DEFAULT '#3b82f6',
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES admin(id) ON DELETE CASCADE,
    UNIQUE (user_id, name)
);
```

---

## 🗂️ Categories Management Endpoints

### 1. `GET /api/v1/admin/categories` — List All Creator Categories

Retrieves all categories owned by the authenticated creator account, ordered by `display_order` (ascending). Dynamically computes `contentCount` (total published videos in each category) or returns a lightweight dropdown list if `simple=true`.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Query Parameters
- `simple` (boolean, optional, default: `false`): When set to `true`, skips the SQL `Video` count join and returns a lightweight array of category dropdown options (`id`, `name`, `slug`).

#### Internal Backend Workflow
1. Extracts `user_id` from creator JWT bearer token context.
2. If `simple=true`:
   - Queries `Category` table for `id`, `name`, `slug` filtering by `user == user_id`, ordered by `display_order.asc()`. Skips SQL `Video` count join.
3. If `simple=false` (default):
   - Executes dynamic SQL `LEFT OUTER JOIN` between `Category` and `Video` tables to aggregate `contentCount` on-the-fly:
   ```python
   query = Category.select(
       Category,
       fn.COUNT(Video.id).alias("content_count")
   ).join(
       Video, on=(Category.slug == Video.category), join_type="LEFT OUTER"
   ).where(
       (Category.user == user_id) &
       (Video.status == "published") &
       (Video.transcoding_status == "READY")
   ).group_by(Category.id).order_by(Category.display_order.asc())
   ```

#### Response Specification (`200 OK`)

##### Scenario A: Full Category List (`simple=false` / default)
```json
{
  "data": [
    {
      "id": 1,
      "name": "Programming",
      "slug": "programming",
      "description": "Software development and engineering tutorials",
      "icon": "💻",
      "color": "#3b82f6",
      "contentCount": 42,
      "order": 1,
      "createdAt": "2024-01-15T08:00:00Z",
      "updatedAt": "2024-06-20T10:30:00Z"
    },
    {
      "id": 2,
      "name": "Design & UI/UX",
      "slug": "design-ui-ux",
      "description": "Figma, mobile UI, and visual design courses",
      "icon": "🎨",
      "color": "#ec4899",
      "contentCount": 18,
      "order": 2,
      "createdAt": "2024-02-01T12:00:00Z",
      "updatedAt": "2024-06-20T10:30:00Z"
    }
  ]
}
```

##### Scenario B: Lightweight Dropdown Options List (`simple=true`)
```json
{
  "data": [
    {
      "id": 1,
      "name": "Programming",
      "slug": "programming"
    },
    {
      "id": 2,
      "name": "Design & UI/UX",
      "slug": "design-ui-ux"
    }
  ]
}
```

---

### 2. `POST /api/v1/admin/categories` — Create Category

Creates a new content category for the authenticated creator account.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "name": "Mobile Development",
  "description": "Flutter, React Native, and iOS Native tutorials",
  "icon": "📱",
  "color": "#10b981"
}
```

#### Validation Rules
* `name`: Required string (1 to 100 characters). Must be unique per creator account.
* `description`: Optional string (max 500 characters).
* `icon`: Optional string emoji or icon string (default: `"📁"`).
* `color`: Optional hex color string (default: `"#3b82f6"`).

#### Internal Backend Workflow
1. Verifies no category with the same name exists for `user_id`.
2. Generates URL-friendly `slug` from category name (`mobile-development`).
3. Auto-calculates `display_order = max(display_order) + 1`.
4. Commits new `Category` record to database.

#### Response Specification (`201 Created`)
```json
{
  "id": 3,
  "name": "Mobile Development",
  "slug": "mobile-development",
  "description": "Flutter, React Native, and iOS Native tutorials",
  "icon": "📱",
  "color": "#10b981",
  "contentCount": 0,
  "order": 3,
  "createdAt": "2026-08-12T00:00:00Z",
  "updatedAt": "2026-08-12T00:00:00Z"
}
```

---

### 3. `PUT /api/v1/admin/categories/{category_id}` — Edit Category

Updates textual fields (`name`, `description`, `icon`, `color`) for an existing category.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `category_id` (integer, required): Database primary key ID of target category.

#### Request Body
```json
{
  "name": "Mobile & Cross Platform",
  "description": "Updated mobile engineering tutorials",
  "icon": "📱",
  "color": "#059669"
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 3,
  "name": "Mobile & Cross Platform",
  "slug": "mobile-cross-platform",
  "description": "Updated mobile engineering tutorials",
  "icon": "📱",
  "color": "#059669",
  "contentCount": 0,
  "order": 3,
  "createdAt": "2026-08-12T00:00:00Z",
  "updatedAt": "2026-08-12T00:00:00Z"
}
```

---

### 4. `DELETE /api/v1/admin/categories/{category_id}` — Delete Category

Deletes a category asset and safely unassigns (`category = null`) videos linked to it.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `category_id` (integer, required): Database primary key ID of category to delete.

#### Internal Backend Workflow
1. Verifies ownership (`Category.user == user_id`).
2. Updates associated videos (`Video.category = null`) so video assets remain intact.
3. Deletes `Category` record from database.

#### Response Specification (`200 OK`)
```json
{
  "message": "Category deleted successfully"
}
```

---

### 5. `PUT /api/v1/admin/categories/reorder` — Reorder Categories (Drag & Drop)

Persists new category display ordering after drag-and-drop actions in the Admin Portal UI.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "ids": [3, 1, 2]
}
```

#### Internal Backend Workflow
1. Receives an ordered array of category primary key IDs.
2. Iterates through array, updating `Category.display_order = index + 1` for each category owned by `user_id` inside an atomic transaction.

#### Response Specification (`200 OK`)
```json
{
  "message": "Category order updated"
}
```
