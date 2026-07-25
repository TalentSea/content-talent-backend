# Creator Admin — Plan Management API Specification

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
  "detail": "Missing required plan name or invalid price."
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
  "detail": "Plan 12 not found"
}
```

#### 4. `422 Unprocessable Entity` — Schema Validation Failure
```json
{
  "detail": [
    {
      "loc": ["body", "price"],
      "msg": "value is not a valid float",
      "type": "type_error.float"
    }
  ]
}
```

#### 5. `500 Internal Server Error` — Database Error
```json
{
  "detail": "Internal server error while processing plan request"
}
```

---

## 💳 Admin Plan Management Endpoints

### 1. `GET /api/v1/plans` — List Creator Plans

Returns a list of plan offerings for the authenticated creator.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Response Specification (`200 OK`)
```json
[
  {
    "id": 12,
    "name": "Premium",
    "price": 29.99,
    "period": "monthly",
    "description": "Unlimited access plus premium support.",
    "features": ["No watermark", "Early access"],
    "active": true,
    "popular": true,
    "subscribers": 420,
    "monthly_revenue": 12595.8,
    "created_at": "2026-01-10T10:00:00Z",
    "updated_at": "2026-06-20T15:30:00Z"
  }
]
```

---

### 2. `GET /api/v1/plans/{plan_id}` — Get Plan Details

Returns full metadata for a single plan.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `plan_id` (integer, required)

#### Response Specification (`200 OK`)
```json
{
  "id": 12,
  "name": "Premium",
  "price": 29.99,
  "period": "monthly",
  "description": "Unlimited access plus premium support.",
  "features": ["No watermark", "Early access"],
  "active": true,
  "popular": true,
  "subscribers": 420,
  "monthly_revenue": 12595.8,
  "created_at": "2026-01-10T10:00:00Z",
  "updated_at": "2026-06-20T15:30:00Z"
}
```

---

### 3. `POST /api/v1/plans` — Create Plan

Creates a new subscription plan.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body
```json
{
  "name": "Starter",
  "price": 9.99,
  "period": "monthly",
  "description": "A lightweight starter plan for new subscribers.",
  "features": ["Access to basic content", "Community support"],
  "active": true,
  "popular": false
}
```

#### Response Specification (`201 Created`)
```json
{
  "id": 15,
  "name": "Starter",
  "price": 9.99,
  "period": "monthly",
  "description": "A lightweight starter plan for new subscribers.",
  "features": ["Access to basic content", "Community support"],
  "active": true,
  "popular": false,
  "subscribers": 0,
  "monthly_revenue": 0.0,
  "created_at": "2026-07-25T08:30:00Z",
  "updated_at": "2026-07-25T08:30:00Z"
}
```

---

### 4. `PUT /api/v1/plans/{plan_id}` — Update Plan

Updates existing plan metadata.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Path Parameters
- `plan_id` (integer, required)

#### Request Body
```json
{
  "price": 34.99,
  "popular": true
}
```

#### Response Specification (`200 OK`)
```json
{
  "id": 12,
  "name": "Premium",
  "price": 34.99,
  "period": "monthly",
  "description": "Unlimited access plus premium support.",
  "features": ["No watermark", "Early access"],
  "active": true,
  "popular": true,
  "subscribers": 420,
  "monthly_revenue": 14595.8,
  "created_at": "2026-01-10T10:00:00Z",
  "updated_at": "2026-07-25T12:00:00Z"
}
```

---

### 5. `DELETE /api/v1/plans/{plan_id}` — Delete Plan

Deletes a plan from the creator’s plan catalog.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `plan_id` (integer, required)

#### Response Specification (`200 OK`)
```json
{
  "status": "success"
}
```

---

### 6. `PATCH /api/v1/plans/{plan_id}/toggle` — Toggle Plan Active State

Toggles a plan between active and inactive.

#### Request Headers
```http
Authorization: Bearer <creator_access_token>
```

#### Path Parameters
- `plan_id` (integer, required)

#### Response Specification (`200 OK`)
```json
{
  "id": 12,
  "active": false,
  "updated_at": "2026-07-25T12:05:00Z"
}
```
```