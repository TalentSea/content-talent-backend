# Creator Admin — Subscriber Management API Specification

## 1. System Architecture & Security Standards

### Authentication Standard
All endpoints require a valid JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <creator_access_token>
```
### Standard HTTP Error Responses

All error responses follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Invalid Request Payload
```json
{
  "detail": "Invalid plan value provided."
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
  "detail": "Subscriber 102 not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "subject"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Database Error
```json
{
  "detail": "Internal server error while processing subscriber request"
}
```

---

## 2. Subscriber Default Field Values

New subscriber records are created with default values that reflect a logged-in user who has not yet purchased any subscription:

- `plan`: `"none"`
- `status`: `"passive"`
- `avatar`: `"none"`

This means the platform will treat the subscriber as a passive user until they choose a paid plan or update their profile.

---

## 📬 Admin Subscriber Management Endpoints

### 1. `GET /api/v1/subscribers/stats` — Subscriber Analytics Summary

Returns aggregated subscriber metrics for the authenticated creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Response Specification (`200 OK`)
```json
{
  "total_subscribers": 184,
  "growth_rate": 12.4,
  "avg_revenue_per_user": 14.8,
  "churn_rate": 3.2
}
```

---

### 2. `GET /api/v1/subscribers/plan-distribution` — Plan Distribution Breakdown

Returns the current subscriber count and percentage for each plan tier.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Response Specification (`200 OK`)
```json
[
  {"plan": "Basic", "count": 102, "percentage": 55.4},
  {"plan": "Pro", "count": 60, "percentage": 32.6},
  {"plan": "Premium", "count": 22, "percentage": 12.0}
]
```

---

### 3. `GET /api/v1/subscribers/recent` — Recent Subscriber Activity

Returns the most recently joined subscribers.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Query Parameters
- `limit` (integer, optional, default: `5`, max: `20`)

#### Example Request URL
```http
GET /api/v1/subscribers/recent?limit=10
```

#### Response Specification (`200 OK`)
```json
[
  {
    "id": 301,
    "name": "Alex Rivera",
    "email": "alex@example.com",
    "plan": "Pro",
    "status": "active",
    "revenue": 14.99,
    "joined_at": "2026-07-19T15:10:00Z",
    "avatar": "https://cdn.example.com/avatars/301.png"
  }
]
```

---

### 4. `GET /api/v1/subscribers` — List Subscribers (Paginated)

Returns a paginated list of subscribers belonging to the authenticated creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Query Parameters
- `page` (integer, optional, default: `1`)
- `limit` (integer, optional, default: `20`, max: `100`)
- `plan` (string, optional)
- `status` (string, optional)
- `join_date_from` (ISO datetime, optional)
- `join_date_to` (ISO datetime, optional)
- `search` (string, optional)

#### Response Specification (`200 OK`)
```json
{
  "total": 184,
  "page": 1,
  "limit": 20,
  "total_pages": 10,
  "items": [
    {
      "id": 205,
      "name": "Maya Chen",
      "email": "maya@example.com",
      "plan": "Premium",
      "status": "active",
      "revenue": 29.99,
      "joined_at": "2026-06-15T10:00:00Z",
      "avatar": "https://cdn.example.com/avatars/205.png"
    }
  ]
}
```

---

### 5. `GET /api/v1/subscribers/{subscriber_id}` — Get Subscriber Profile

Returns subscriber details and activity metadata.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `subscriber_id` (integer, required)

#### Response Specification (`200 OK`)
```json
{
  "id": 205,
  "name": "Maya Chen",
  "email": "maya@example.com",
  "plan": "Premium",
  "status": "active",
  "total_revenue": 329.75,
  "revenue": 29.99,
  "joined_at": "2026-06-15T10:00:00Z",
  "last_active_at": "2026-07-24T12:38:00Z",
  "avatar": "https://cdn.example.com/avatars/205.png"
}
```

---

### 6. `PUT /api/v1/subscribers/{subscriber_id}/plan` — Update Subscriber Plan

Updates the subscriber’s current plan tier.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `subscriber_id` (integer, required)

#### Request Body
```json
{
  "plan": "Premium"
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 205,
  "name": "Maya Chen",
  "email": "maya@example.com",
  "plan": "Premium",
  "status": "active",
  "total_revenue": 329.75,
  "revenue": 29.99,
  "joined_at": "2026-06-15T10:00:00Z",
  "last_active_at": "2026-07-24T12:38:00Z",
  "avatar": "https://cdn.example.com/avatars/205.png"
}
```

---

### 7. `POST /api/v1/subscribers/{subscriber_id}/email` — Send Email to Subscriber

Sends a direct message to the selected subscriber.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "subject": "Welcome to Premium",
  "body": "Your plan has been upgraded to Premium with access to exclusive releases."
}
```

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 8. `PUT /api/v1/subscribers/{subscriber_id}/suspend` — Suspend Subscriber

Temporarily suspends the subscriber account with an optional reason.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "reason": "Payment issue detected"
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 205,
  "name": "Maya Chen",
  "email": "maya@example.com",
  "plan": "Premium",
  "status": "suspended",
  "total_revenue": 329.75,
  "revenue": 29.99,
  "joined_at": "2026-06-15T10:00:00Z",
  "last_active_at": "2026-07-24T12:38:00Z",
  "avatar": "https://cdn.example.com/avatars/205.png"
}
```

---

### 9. `PUT /api/v1/subscribers/{subscriber_id}/reinstate` — Reinstate Subscriber

Reactivates a suspended subscriber account.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Response Specification (`200 OK`)
```json
{
  "id": 205,
  "name": "Maya Chen",
  "email": "maya@example.com",
  "plan": "Premium",
  "status": "active",
  "total_revenue": 329.75,
  "revenue": 29.99,
  "joined_at": "2026-06-15T10:00:00Z",
  "last_active_at": "2026-07-24T12:38:00Z",
  "avatar": "https://cdn.example.com/avatars/205.png"
}
```