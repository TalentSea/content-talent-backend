# Admin Subscription Plans Management API Specification

This document details the RESTful API endpoints for Web Admin Creators to configure, price, and customize their two fixed Subscription Plan Tiers displayed on the mobile application paywall checkout screen.

---

## 1. System Architecture & Two-Tier Business Model

### 1.1 Strict Two-Tier Subscription Model

The platform enforces a standardized, multi-tenant **Two-Tier Architecture** provisioned atomically during tenant studio onboarding (via the Platform Super Admin Web Dashboard or `POST /api/v1/admin/tenants`):

1. **Tier 1 (`plan_type = "with_ads"` / `display_order = 1`)**: Standard with Ads tier.
2. **Tier 2 (`plan_type = "no_ads"` / `display_order = 2`)**: Premium Ad-Free tier.

### 1.2 Built-in Platform Features (`app/constants/plans.py`)

Feature checklists describe the platform's technical streaming capabilities and are maintained centrally in `app/constants/plans.py`. When API endpoints serve plan details to the web admin portal or mobile app, the backend dynamically attaches the corresponding feature list:

- **Tier 1 (`with_ads`) Features**:
  - Full access to all videos & shorts
  - High-definition (HD) streaming
  - Watch on Android phone & tablet
  - Includes ads on videos (Shorts are ad-free)
- **Tier 2 (`no_ads`) Features**:
  - Full access to all videos & shorts
  - High-definition (HD) streaming
  - Watch on Android phone & tablet
  - 100% Ad-free on all videos & shorts

> [!NOTE]
> Creators **do not** create or edit technical feature bullets. Technical entitlements (ad-insertion, resolution, downloads, concurrent screen limits) are platform-governed.

### 1.3 ocalization & Pricing Standards

- **Default Currency**: `"INR"` (Indian Rupee ₹).
- **Discount Calculation**:
  $$\text{final\_price} = \text{base\_price} \times \left(1 - \frac{\text{discount\_percentage}}{100}\right)$$
- **Billing Period**: Standardized monthly billing (`billing_period_value = 1`, `billing_period_unit = "months"`).

---

## 2. Standard HTTP Error Responses

All error responses follow the standard FastAPI JSON error envelope:

#### 1. `400 Bad Request` — Validation / Invalid Value

```json
{
  "detail": "Discount percentage must be between 0 and 100"
}
```

#### 2. `401 Unauthorized` — Missing or Invalid Token

```json
{
  "detail": "Could not validate credentials"
}
```

#### 3. `403 Forbidden` — Role Mismatch

```json
{
  "detail": "Forbidden: Admin portal authorization required"
}
```

#### 4. `404 Not Found` — Plan Not Found or Belongs to Another Creator

```json
{
  "detail": "Subscription plan 104 not found"
}
```

---

## 3. API Endpoint Specifications

### 3.1 `GET /api/v1/admin/plans` — List Creator Subscription Plans

Retrieves the 2 fixed subscription plans owned by the authenticated creator studio, enriched with built-in feature lists from `app/constants/plans.py` and live subscriber and monthly revenue metrics.

#### Headers

```http
Cookie: admin_access_token=<admin_access_token>  (Primary: Browser)
Authorization: Bearer <admin_access_token>       (Fallback: Testing/Tooling)
```

#### Response Envelope (`200 OK`)

```json
[
  {
    "id": 1,
    "plan_type": "with_ads",
    "name": "Standard with Ads",
    "description": "Access to our full catalog with occasional commercial breaks.",
    "base_price": 99.0,
    "discount_percentage": 0.0,
    "final_price": 99.0,
    "currency": "INR",
    "billing_period_value": 1,
    "billing_period_unit": "months",
    "features": [
      "Full access to all videos & shorts",
      "High-definition (HD) streaming",
      "Watch on Android phone & tablet",
      "Includes ads on videos (Shorts are ad-free)"
    ],
    "badge_text": "Popular",
    "display_order": 1,
    "active_subscribers": 142,
    "monthly_revenue": 14058.0,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-09-14T12:00:00Z"
  },
  {
    "id": 2,
    "plan_type": "no_ads",
    "name": "Premium Ad-Free",
    "description": "Enjoy completely uninterrupted premium streaming in full HD.",
    "base_price": 199.0,
    "discount_percentage": 10.0,
    "final_price": 179.1,
    "currency": "INR",
    "billing_period_value": 1,
    "billing_period_unit": "months",
    "features": [
      "Full access to all videos & shorts",
      "High-definition (HD) streaming",
      "Watch on Android phone & tablet",
      "100% Ad-free on all videos & shorts"
    ],
    "badge_text": "Best Value",
    "display_order": 2,
    "active_subscribers": 310,
    "monthly_revenue": 55521.0,
    "created_at": "2026-08-20T10:00:00Z",
    "updated_at": "2026-09-14T12:00:00Z"
  }
]
```

---

### 3.2 `PUT /api/v1/admin/plans/{plan_id}` — Update Subscription Plan Pricing & Copy

Saves creator customizations for a plan tier from the Edit modal. The backend automatically recomputes `final_price` and preserves the built-in features and technical tier identity.

#### Headers

```http
Cookie: admin_access_token=<admin_access_token>  (Primary: Browser)
Authorization: Bearer <admin_access_token>       (Fallback: Testing/Tooling)
Content-Type: application/json
```

#### Request Payload

```json
{
  "name": "Fan Pass (With Ads)",
  "description": "Watch all my videos with occasional short ads",
  "base_price": 129.0,
  "discount_percentage": 15.0,
  "badge_text": "MOST POPULAR"
}
```

_(All fields are optional. Unsupplied fields retain their current database values)._

#### Response Envelope (`200 OK`)

```json
{
  "id": 1,
  "plan_type": "with_ads",
  "name": "Fan Pass (With Ads)",
  "description": "Watch all my videos with occasional short ads",
  "base_price": 129.0,
  "discount_percentage": 15.0,
  "final_price": 109.65,
  "currency": "INR",
  "billing_period_value": 1,
  "billing_period_unit": "months",
  "features": [
    "Full access to all videos & shorts",
    "High-definition (HD) streaming",
    "Watch on Android phone & tablet",
    "Includes ads on videos (Shorts are ad-free)"
  ],
  "badge_text": "MOST POPULAR",
  "display_order": 1,
  "active_subscribers": 142,
  "monthly_revenue": 15570.3,
  "created_at": "2026-08-20T10:00:00Z",
  "updated_at": "2026-09-14T12:15:00Z"
}
```
