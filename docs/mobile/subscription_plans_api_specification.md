# Mobile Subscriber — Subscription Plans API Specification

This document details the RESTful API endpoint for Mobile Subscribers and Guest Users to retrieve active creator subscription tiers for the checkout paywall screen.

---

## 1. System Architecture & Security Standards

### 1.1 Base Route Prefix
```http
/api/v1/mobile/plans
```

### 1.2 Authentication & Authorization
* **Public & Protected Access**: Accessible by both **Guest Users** and **Authenticated Subscribers** using `get_current_subscriber`.
```http
Authorization: Bearer <subscriber_access_token>
```
* **Creator Multi-Tenancy**: The endpoint automatically filters plans for the subscriber's bound creator studio (`creator_id`).
* **Active Status Filter**: Only plans where `is_active = true` are returned to mobile subscribers.

---

## 2. API Endpoint Specification

### 2.1 `GET /api/v1/mobile/plans` — List Active Subscription Plans Feed

Retrieves active creator subscription plan tiers sorted by `display_order` ascending for mobile paywall checkout.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
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
    "display_order": 1
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
    "display_order": 2
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
    "display_order": 3
  }
]
```

---

## 3. Error Responses

#### `401 Unauthorized`
```json
{
  "detail": "Could not validate credentials"
}
```
