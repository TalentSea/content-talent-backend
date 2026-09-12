---
name: razorpay-subscription-billing
description: Architectural standards for Razorpay order generation, HMAC-SHA256 payment signature verification, webhook ingestion, subscription plan curation, entitlement state machines, and automated subscription expiration background loops.
---

# Razorpay Payments & Subscription Entitlements Skill

## Overview
This skill documents technical standards, cryptographic signature validations, webhook security, and subscription lifecycle management for the Razorpay payment gateway integration in the OTT platform backend.

---

## 1. Domain Entities & State Machine

The billing and entitlement subsystem operates across three core Peewee entities:

```
┌────────────────────────┐      ┌────────────────────────┐      ┌────────────────────────┐
│    SubscriptionPlan    │      │        Payment         │      │    UserSubscription    │
├────────────────────────┤      ├────────────────────────┤      ├────────────────────────┤
│ • name, plan_type      │      │ • razorpay_order_id    │      │ • subscriber, creator  │
│ • price, discount_pct  │◄─────┤ • razorpay_payment_id  │─────►│ • plan, start_date     │
│ • duration_days        │      │ • status (created,     │      │ • end_date             │
│ • is_active            │      │   captured, failed)    │      │ • status (active,      │
└────────────────────────┘      └────────────────────────┘      │   expired, cancelled)  │
                                                                └────────────────────────┘
```

### Plan Types & Duration Standards
* `monthly`: 30 days duration.
* `quarterly`: 90 days duration.
* `yearly`: 365 days duration.

---

## 2. Server-Side Order Creation Flow (`POST /payments/create-order`)

Clients MUST NEVER create orders directly with Razorpay. Orders must be initiated server-side:

1. **Plan Validation**: Retrieve active plan by `plan_id`. If `is_active == False` or plan not found, return `HTTP 404 Not Found`.
2. **Amount Calculation**: Calculate final payable amount in paise (1 INR = 100 paise), accounting for `discount_percentage`.
3. **Razorpay REST API Call**:
   - URL: `https://api.razorpay.com/v1/orders`
   - Authentication: HTTP Basic Auth `(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)`.
   - Payload:
     ```json
     {
       "amount": 29900,
       "currency": "INR",
       "receipt": "rcpt_{subscriber_id}_{timestamp}",
       "notes": {
         "subscriber_id": 12,
         "plan_id": 3,
         "creator_id": 1
       }
     }
     ```
4. **Payment Record Persistence**: Store an initial record in `payments` table with `status = "created"`.

---

## 3. Cryptographic Signature Verification (`POST /payments/verify`)

Before granting subscription access, the server MUST verify the client-provided Razorpay payment signature using HMAC-SHA256:

### Verification Algorithm
```python
import hmac
import hashlib

data_to_sign = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}"
expected_signature = hmac.new(
    settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
    data_to_sign.encode("utf-8"),
    hashlib.sha256,
).hexdigest()

if not hmac.compare_digest(expected_signature, payload.razorpay_signature):
    raise HTTPException(status_code=400, detail="INVALID_PAYMENT_SIGNATURE")
```

### Post-Verification Entitlement Grant
Upon successful signature validation:
1. Update `Payment.status = "captured"`, saving `razorpay_payment_id` and `razorpay_signature`.
2. Calculate subscription window:
   - `start_date = now`
   - `end_date = now + timedelta(days=plan.duration_days)`
3. Create or renew `UserSubscription`:
   - Set `status = "active"`.
   - If the user already has an active subscription, extend `end_date` from the current `end_date` rather than resetting from today.

---

## 4. Webhook Ingestion & Idempotency (`POST /webhooks/razorpay`)

Webhooks handle asynchronous payments (UPI intent, netbanking redirects) and out-of-band events:

### Webhook Signature Validation
* Header: `X-Razorpay-Signature`
* Validation: Compute HMAC-SHA256 over raw request body using `RAZORPAY_WEBHOOK_SECRET`.
* Reject invalid signatures with `HTTP 400 Bad Request`.

### Idempotency Standard
Webhook handlers must be strictly idempotent:
* If a payment with `razorpay_order_id` is already marked `"captured"`, acknowledge with `HTTP 200 OK` without creating duplicate subscriptions.
* Handle both `order.paid` and `payment.captured` events gracefully.

---

## 5. Automated Subscription Expiration Worker

To prevent subscribers from retaining access past their paid duration:

* **Background Task**: `scheduled_subscription_expiration_worker()` runs in the FastAPI lifespan context.
* **Interval**: Configured via `SUBSCRIPTION_EXPIRATION_LOOP_INTERVAL_SECONDS` (default: `3600s` / 1 hour).
* **Atomic Query**:
  ```python
  now = datetime.now(timezone.utc)
  UserSubscription.update(status="expired").where(
      (UserSubscription.status == "active") & (UserSubscription.end_date < now)
  ).execute()
  ```

---

## 6. Environment Configuration Reference

| Environment Variable | Type | Purpose |
| :--- | :---: | :--- |
| `RAZORPAY_KEY_ID` | `str` | Razorpay public key identifier for API authentication. |
| `RAZORPAY_KEY_SECRET` | `str` | Razorpay secret key used for HMAC signature validation. |
| `RAZORPAY_WEBHOOK_SECRET` | `str` | Webhook secret for verifying `X-Razorpay-Signature`. |
| `SUBSCRIPTION_EXPIRATION_LOOP_INTERVAL_SECONDS` | `int` | Interval in seconds for the subscription expiration background loop. |
