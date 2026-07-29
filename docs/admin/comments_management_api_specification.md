# Creator Admin — Comments API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints require a valid JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <creator_access_token>
```
The creator identity (`user_id`) is extracted directly from the authenticated session context on the backend (`Depends(get_current_user)`). Creators can only access, reply to, like, and delete comments associated with their own content assets.

### Architecture Overview
- **Backend Service**: FastAPI (Python) handles authentication, request validation, state management, comment replies, likes, and deletion logic.
- **Database**: Relational Database (Peewee ORM) stores comments, replies, video associations, and the unified `comment_likes` junction table (tracking unique `user_id` + `comment_id` likes for both creators and subscribers).

### Standard HTTP Error Responses
All error responses follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid Request Payload
```json
{
  "detail": "Comment text cannot be empty."
}
```

#### 2. `401 Unauthorized` — Missing or Expired JWT Token
```json
{
  "detail": "Could not validate credentials"
}
```

#### 3. `404 Not Found` — Comment Not Found
```json
{
  "detail": "Comment 1052 not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Database Error
```json
{
  "detail": "Internal server error while processing comment request"
}
```

---

## 💬 Admin Comments Endpoints

### 1. `GET /api/v1/admin/comments` — List Top-Level Comments (Paginated & Filtered)

Retrieves a paginated list of top-level comments across the creator's videos with support for text search, video/category filtering, minimum likes, and total `reply_count`.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Request Query Parameters

| Param | Type | Required | Description |
|---|---|---|---|
| `category` | `string` | No | Filter comments by video category ID |
| `videoId` | `integer` | No | Filter comments by specific video ID |
| `date` | `string` | No | Filter comments created on an ISO date (`YYYY-MM-DD`) |
| `minLikes` | `integer` | No | Filter comments with at least N likes |
| `search` | `string` | No | Search substring within comment body text |
| `sort` | `string` | No | Sort order: `newest` (default), `oldest`, `mostLiked` |
| `page` | `integer` | No | Page number (default `1`) |
| `limit` | `integer` | No | Items per page (default `20`, max `100`) |

#### Response Specification (`200 OK`)
```json
{
  "total": 12450,
  "page": 1,
  "limit": 20,
  "total_pages": 623,
  "items": [
    {
      "id": 8912,
      "user_id": 4512,
      "user_name": "Sarah Connor",
      "user_avatar": "https://talentsea77999.b-cdn.net/avatars/user_4512.jpg",
      "text": "Great explanation on FastAPI dependency injection!",
      "video_id": 102,
      "video_title": "FastAPI Masterclass - Part 3",
      "likes": 42,
      "is_liked": true,
      "reply_count": 14,
      "created_at": "2024-06-18T14:22:00Z"
    }
  ]
}
```

---

### 2. `GET /api/v1/admin/comments/{id}/replies` — Fetch Thread Replies (Paginated)

Retrieves a paginated list of child replies nested under a specific top-level comment when the creator clicks "Show all replies".

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `id` (integer, required): ID of the top-level parent comment.

#### Request Query Parameters

| Param | Type | Required | Description |
|---|---|---|---|
| `sort` | `string` | No | Sort order: `oldest` (default, thread chronological order) or `newest` |
| `page` | `integer` | No | Page number (default `1`) |
| `limit` | `integer` | No | Items per page (default `20`, max `100`) |

#### Response Specification (`200 OK`)
```json
{
  "total": 14,
  "page": 1,
  "limit": 20,
  "total_pages": 1,
  "items": [
    {
      "id": 9001,
      "comment_id": 8912,
      "text": "Thank you Sarah! Glad you found it useful.",
      "user_id": 101,
      "user_name": "Alex Tech",
      "user_avatar": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_101_1785055000.jpg",
      "created_at": "2024-06-18T15:00:00Z"
    },
    {
      "id": 9002,
      "comment_id": 8912,
      "text": "Also checking if there is a follow-up video on async handlers?",
      "user_id": 4512,
      "user_name": "Sarah Connor",
      "user_avatar": "https://talentsea77999.b-cdn.net/avatars/user_4512.jpg",
      "created_at": "2024-06-18T15:30:00Z"
    }
  ]
}
```

---

### 3. `POST /api/v1/admin/comments/{id}/reply` — Post Creator Reply

Posts an official creator reply to a specific user comment.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `id` (integer, required): ID of the parent comment being replied to.

#### Request Body
```json
{
  "text": "Thanks for your feedback! Part 4 is coming out tomorrow."
}
```

#### Response Specification (`201 Created`)
```json
{
  "id": 9105,
  "comment_id": 8912,
  "text": "Thanks for your feedback! Part 4 is coming out tomorrow.",
  "user_id": 101,
  "user_name": "Alex Tech",
  "user_avatar": "https://talentsea77999.b-cdn.net/assets/avatars/avatar_101_1785055000.jpg",
  "created_at": "2024-06-20T10:30:00Z"
}
```

---

### 4. `POST /api/v1/admin/comments/{id}/like` — Toggle Comment Like

Toggles authenticated user's like state in the `comment_likes` table, updating likes count and `is_liked` status.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `id` (integer, required): ID of the comment to like/unlike.

#### Request Body — None

#### Response Specification (`200 OK`)

##### Scenario A: Comment Liked (Toggled ON)
```json
{
  "status": "success",
  "is_liked": true,
  "likes": 43
}
```

##### Scenario B: Comment Un-liked (Toggled OFF)
```json
{
  "status": "success",
  "is_liked": false,
  "likes": 42
}
```

---

### 5. `DELETE /api/v1/admin/comments/{id}` — Delete Comment

Deletes a comment permanently from a creator's video.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `id` (integer, required): ID of the comment to remove.

#### Request Body — None

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```
