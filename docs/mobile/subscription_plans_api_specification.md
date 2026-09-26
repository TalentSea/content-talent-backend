# Mobile Subscriber — Subscription Plans API Specification

This document details the RESTful API endpoint for Mobile Subscribers and Guest Users to retrieve active creator subscription tiers for the checkout paywall screen.

---

## 1. System Architecture & Two-Tier Business Model

### 1.1 Base Route Prefix
```http
/api/v1/mobile/plans
```

### 1.2 Authentication & Authorization
* **Public & Protected Access**: Accessible by both **Guest Users** and **Authenticated Subscribers** using `get_current_subscriber`.
```http
Authorization: Bearer <subscriber_access_token>
```
* **Creator Multi-Tenancy**: The endpoint automatically filters plans for the subscriber's bound creator studio (`tenant_id`).

### 1.3 Standardized Two-Tier OTT Architecture
The platform enforces a standardized two-tier OTT subscription paywall provisioned for every creator:
1. **Tier 1 (`plan_type = "with_ads"`, `display_order = 1`)**: Standard ad-supported tier.
2. **Tier 2 (`plan_type = "no_ads"`, `display_order = 2`)**: Premium ad-free streaming & offline download tier.

### 1.4 Dynamic Platform Features (`app/constants/plans.py`)
Technical streaming entitlements (resolution, offline download availability, concurrent screens, and ad insertion policy) are maintained centrally in `app/constants/plans.py`. When mobile clients fetch the paywall feed, the backend dynamically injects the appropriate feature bullet list into the response:

* **With-Ads Tier Features**:
  * Full access to all videos & shorts
  * High-definition (HD) streaming
  * Watch on Android phone & tablet
  * Includes ads on videos (Shorts are ad-free)
* **No-Ads Tier Features**:
  * Full access to all videos & shorts
  * High-definition (HD) streaming
  * Watch on Android phone & tablet
  * 100% Ad-free on all videos & shorts

---

## 2. API Endpoint Specification

### 2.1 `GET /api/v1/mobile/plans` — List Subscription Plans Feed

Retrieves creator subscription plan tiers sorted by `display_order` ascending for mobile paywall checkout.

#### Request Headers
```http
Authorization: Bearer <subscriber_access_token>
```

#### Response Envelope (`200 OK`)
```json
[
  {
    "id": 1,
    "plan_type": "with_ads",
    "name": "Standard with Ads",
    "description": "Stream unlimited content with occasional ads",
    "base_price": 499.00,
    "discount_percentage": 0.0,
    "final_price": 499.00,
    "currency": "INR",
    "billing_period_value": 1,
    "billing_period_unit": "months",
    "features": [
      "Full access to all videos & shorts",
      "High-definition (HD) streaming",
      "Watch on Android phone & tablet",
      "Includes ads on videos (Shorts are ad-free)"
    ],
    "badge_text": null,
    "display_order": 1
  },
  {
    "id": 2,
    "plan_type": "no_ads",
    "name": "Premium Ad-Free",
    "description": "Enjoy crystal-clear streaming without interruptions",
    "base_price": 999.00,
    "discount_percentage": 10.0,
    "final_price": 899.10,
    "currency": "INR",
    "billing_period_value": 1,
    "billing_period_unit": "months",
    "features": [
      "Full access to all videos & shorts",
      "High-definition (HD) streaming",
      "Watch on Android phone & tablet",
      "100% Ad-free on all videos & shorts"
    ],
    "badge_text": "POPULAR",
    "display_order": 2
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
