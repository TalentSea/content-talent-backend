# Admin Subscription Plans Management API Specification

This document details the RESTful API endpoints for Web Admin Creators to configure, manage, edit, reorder, and curate Subscription Plan Tiers displayed on the mobile application paywall checkout screen.

---

## 1. System Architecture & Security Standards

### 1.1 Base Route Prefix
```http
/api/v1/admin/plans
```

### 1.2 Authentication & Authorization
* All endpoints require a valid Admin Creator JWT Bearer token passed in the HTTP request header:
```http
Authorization: Bearer <admin_access_token>
```
* **Multi-Tenant Isolation**: Extracted `current_user["user_id"]` guarantees creators can only view, create, edit, reorder, or delete subscription plans belonging to their own creator studio.

### 1.3 Localization & Pricing Standards
* **Default Currency**: `"INR"` (Indian Rupee ₹).
* **Discount Calculation**:
  $$\text{final\_price} = \text{base\_price} \times \left(1 - \frac{\text{discount\_percentage}}{100}\right)$$
* **Billing Period Standards**:
  - `billing_period_value`: Positive integer (e.g. `7`, `1`, `12`, `24`).
  - `billing_period_unit`: `"days"`, `"months"`, or `"years"`.

---

## 2. Standard HTTP Error Responses

All error responses across all endpoints follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Schema Validation / Invalid Value
```json
{
  "detail": "Subscription plan with name 'Basic' already exists for this creator studio"
}
```

#### 2. `401 Unauthorized` — Missing or Invalid Bearer Token
```json
{
  "detail": "Could not validate credentials"
}
```

#### 3. `404 Not Found` — Resource Not Found or Forbidden Ownership
```json
{
  "detail": "Subscription plan 104 not found"
}
```

---

## 3. API Endpoint Specifications

### 3.1 `GET /api/v1/admin/plans` — List All Creator Subscription Plans

Retrieves all subscription plans owned by the authenticated creator studio (both active and inactive), ordered by `display_order` ascending, enriched with live active subscriber counts and monthly revenue stats in ₹ INR.

#### Headers
```http
Authorization: Bearer <admin_access_token>
```

#### Response Envelope (`200 OK`)
```json
[
  {
    "id": 1,
    "name": "Basic",
    "description": "Perfect for getting started",
    "base_price": 799.00,
    "discount_percentage": 0.0,
    "final_price": 799.00,
    "currency": "INR",
    "billing_period_value": 1,
    "billing_period_unit": "months",
    "features": [
      "Access to basic content library",
      "Standard video quality",
      "Community access",
      "Email support"
    ],
    "badge_text": null,
    "is_active": true,
    "display_order": 1,
    "active_subscribers": 4309,
    "monthly_revenue": 3442891.00,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-29T12:00:00Z"
  },
  {
    "id": 2,
    "name": "Premium",
    "description": "Best for serious learners",
    "base_price": 2499.00,
    "discount_percentage": 0.0,
    "final_price": 2499.00,
    "currency": "INR",
    "billing_period_value": 24,
    "billing_period_unit": "months",
    "features": [
      "Access to all premium content",
      "4K video quality",
      "Priority community access",
      "Live Q&A sessions",
      "Downloadable resources",
      "24/7 priority support"
    ],
    "badge_text": "⚡",
    "is_active": true,
    "display_order": 2,
    "active_subscribers": 8234,
    "monthly_revenue": 16460000.00,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-29T12:00:00Z"
  },
  {
    "id": 3,
    "name": "Annual Basic",
    "description": "Save 15% with annual billing",
    "base_price": 7999.00,
    "discount_percentage": 15.0,
    "final_price": 6799.15,
    "currency": "INR",
    "billing_period_value": 1,
    "billing_period_unit": "years",
    "features": [
      "All Basic plan features",
      "2 months free",
      "Annual exclusive content"
    ],
    "badge_text": "15% OFF",
    "is_active": true,
    "display_order": 3,
    "active_subscribers": 1245,
    "monthly_revenue": 8465000.00,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-08-29T12:00:00Z"
  }
]
```

---

### 3.2 `POST /api/v1/admin/plans` — Create Subscription Plan

Creates a new subscription plan tier for the creator studio from the Create Plan modal.

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Payload
```json
{
  "name": "Annual Basic",
  "base_price": 7999.00,
  "discount_percentage": 15.0,
  "billing_period_value": 1,
  "billing_period_unit": "years",
  "description": "Save 15% with annual billing",
  "features": [
    "All Basic plan features",
    "2 months free",
    "Annual exclusive content"
  ],
  "badge_text": "15% OFF",
  "is_active": true
}
```

#### Response Envelope (`201 Created`)
```json
{
  "id": 3,
  "name": "Annual Basic",
  "description": "Save 15% with annual billing",
  "base_price": 7999.00,
  "discount_percentage": 15.0,
  "final_price": 6799.15,
  "currency": "INR",
  "billing_period_value": 1,
  "billing_period_unit": "years",
  "features": [
    "All Basic plan features",
    "2 months free",
    "Annual exclusive content"
  ],
  "badge_text": "15% OFF",
  "is_active": true,
  "display_order": 3,
  "active_subscribers": 0,
  "monthly_revenue": 0.00,
  "created_at": "2026-08-29T21:00:00Z",
  "updated_at": "2026-08-29T21:00:00Z"
}
```

---

### 3.3 `PUT /api/v1/admin/plans/{plan_id}` — Update Subscription Plan

Saves edits to an existing subscription plan tier (*Save Changes* button in Edit Modal).

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Payload
```json
{
  "name": "Annual Basic Plus",
  "base_price": 7999.00,
  "discount_percentage": 20.0,
  "billing_period_value": 1,
  "billing_period_unit": "years",
  "description": "Save 20% with annual billing",
  "features": [
    "All Basic plan features",
    "2 months free",
    "Annual exclusive content",
    "Bonus cheat-sheets"
  ],
  "badge_text": "20% OFF",
  "is_active": true
}
```

#### Response Envelope (`200 OK`)
```json
{
  "id": 3,
  "name": "Annual Basic Plus",
  "description": "Save 20% with annual billing",
  "base_price": 7999.00,
  "discount_percentage": 20.0,
  "final_price": 6399.20,
  "currency": "INR",
  "billing_period_value": 1,
  "billing_period_unit": "years",
  "features": [
    "All Basic plan features",
    "2 months free",
    "Annual exclusive content",
    "Bonus cheat-sheets"
  ],
  "badge_text": "20% OFF",
  "is_active": true,
  "display_order": 3,
  "active_subscribers": 1245,
  "monthly_revenue": 8465000.00,
  "created_at": "2026-08-20T10:00:00Z",
  "updated_at": "2026-08-29T21:05:00Z"
}
```

---

### 3.4 `DELETE /api/v1/admin/plans/{plan_id}` — Delete Subscription Plan

Deletes a subscription plan tier (trash bin icon).

#### Headers
```http
Authorization: Bearer <admin_access_token>
```

#### Response Envelope (`200 OK`)
```json
{
  "status": "success",
  "message": "Subscription plan 3 deleted successfully"
}
```

---

### 3.5 `PATCH /api/v1/admin/plans/{plan_id}/toggle-active` — Quick Toggle Active Status

Toggles `is_active` (`true`/`false`) without requiring the full modal payload.

#### Headers
```http
Authorization: Bearer <admin_access_token>
```

#### Response Envelope (`200 OK`)
```json
{
  "id": 1,
  "name": "Basic",
  "is_active": false,
  "updated_at": "2026-08-29T21:10:00Z"
}
```

---

### 3.6 `PUT /api/v1/admin/plans/reorder` — Reorder Display Sequence

Atomically updates display order sequence for subscription plan cards on the admin grid.

#### Headers
```http
Authorization: Bearer <admin_access_token>
Content-Type: application/json
```

#### Request Payload
```json
{
  "ids": [2, 1, 3]
}
```

#### Response Envelope (`200 OK`)
```json
{
  "status": "success",
  "message": "Subscription plan order updated"
}
```
