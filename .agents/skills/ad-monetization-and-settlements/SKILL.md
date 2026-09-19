---
name: ad-monetization-and-settlements
description: Technical standards for Creator Ad Monetization, in-stream Google IMA VAST telemetry beacons, 10-second rapid-fire debouncing, dynamic eCPM resolution, 30% white-label platform commission deduction, bank payout profiles, and CLI monthly revenue reconciliation.
---

# Creator Ad Monetization & Monthly Revenue Settlement Skill

## Overview
This skill establishes production architecture, fraud prevention, and accounting standards for **Video Ad Monetization and Monthly Revenue Settlements** on the white-labeled OTT platform.

---

## 1. Zero-Trust Ad Telemetry & Anti-Spam Ingestion

Mobile video players streaming on the `with_ads` standard tier render advertisements via the **Google Interactive Media Ads (IMA) SDK**. Upon reaching viewability milestones, client players dispatch beacons to `POST /api/v1/mobile/videos/{video_id}/ad-impression`.

### Telemetry Calling Rules
1. **The Primary Trigger (`AdEvent.IMPRESSION`)**:
   - Dispatched the exact moment Google IMA fires `IMPRESSION` (at the **2-second** continuous viewable playback mark).
   - This single beacon officializes the ad as billable in the creator's monthly revenue ledger.
2. **Milestone Events (`midpoint`, `complete`)**:
   - Acknowledged with `HTTP 204 No Content` for player sync, but **do not increment** billable impression rows to prevent duplicate or inflated counting.
3. **Skipped Ads (`AdEvent.SKIPPED`)**:
   - Skippable ads have a 5-second countdown. Because the 2-second viewability mark was already logged at second 2, the impression is monetized. The mobile app transitions to content and does NOT send another beacon.
4. **Early Exit (< 2 seconds)**:
   - If the user closes the video before 2 seconds, Google IMA never fires `IMPRESSION`, and no beacon is dispatched.

### Anti-Spam & Fraud Prevention Pipeline
The backend executes 5 zero-trust security checks before writing to `ad_impression_events`:
```
[ Incoming Ad Impression Beacon ]
               │
               ▼
   [ Gate 1: Role == 'subscriber'? ] ──────────── No ───► HTTP 403 Forbidden
               │ Yes
               ▼
   [ Gate 2: Video exists & published? ] ──────── No ───► HTTP 404 Not Found
               │ Yes
               ▼
   [ Gate 2.5: Creator exists & is_active? ] ──── No ───► Return 204 (Deactivated Creator No-Op)
               │ Yes
               ▼
   [ Gate 3: event_type == 'impression'? ] ────── No ───► Return 204 (Graceful No-Op)
               │ Yes
               ▼
   [ Gate 4: Debounce >= AD_DEBOUNCE_SECONDS? ] ─ No ───► Return 204 (Debounced)
               │ Yes
               ▼
   [ Gate 5: Recent Count < MAX_PER_SESSION? ] ── No ───► Return 204 (Rate Capped)
               │ Yes
               ▼
   [ Log AdImpressionEvent & Return 204 No Content ]
```

* **Rapid-Fire Debounce (`AD_IMPRESSION_DEBOUNCE_SECONDS = 10`)**: Accommodates legitimate back-to-back podded ads (15–30s apart) while dropping accidental network retries or loop spam.
* **Session Rate Cap (`AD_IMPRESSION_MAX_PER_SESSION = 10` per 30 mins)**: Protects against automated script farms and looping bots.

---

## 2. Dynamic eCPM Resolution Standard (Zero Hardcoded Rates)

To maintain absolute financial integrity and avoid legal misrepresentation:

* **Zero Hardcoded Default eCPM**: Never use arbitrary static numbers (e.g. ₹180.00).
* **Brand-New Creators (0 prior payouts)**:
  - Estimated earnings and eCPM MUST return `null`.
  - Monthly status is marked `"accruing"`.
  - The UI presents a truthful *"Accruing (Pending Month 1 Reconciliation)"* badge.
  - Actual impression counters are 100% factual and grow in real time.
* **Established Creators ($\ge 1$ prior payout)**:
  - Dynamically use their **latest settled net eCPM** as the baseline:
    $$\text{Estimated Earnings} = \frac{\text{Active Month Impressions} \times \text{Latest Settled eCPM}}{1000}$$
  - Seamlessly adopts real market advertiser spend.

---

## 3. Discreet 30% White-Label Platform Commission Architecture

The platform charges a 30% technology commission on ad revenue (`PLATFORM_AD_COMMISSION_PERCENT = 30.0`):

1. **Invisible Margin Enforcement**:
   - Commission is deducted strictly at the eCPM layer:
     $$\text{Creator Net eCPM} = \text{Gross eCPM} \times \left(1 - \frac{\text{PLATFORM\_AD\_COMMISSION\_PERCENT}}{100}\right)$$
   - Internal figures (`gross_revenue`, `platform_commission_pct`, `platform_fee`) are stored in the database for financial audit trails, but are **strictly excluded** from creator-facing DTOs and APIs (`/summary`, `/analytics`, `/settlements`).
2. **Creator Studio View**:
   - Creators only see their **Net eCPM** and **Net Payout**.
   - The white-label OTT customer experiences a dedicated platform without platform commission friction.

---

## 4. Bank Payout Profile Standards

Creator bank wire details are managed via `GET / PUT /api/v1/admin/monetization/settings`:

1. **Fields Stored**:
   - `account_holder_name` (alphanumeric string)
   - `account_number` (strictly numeric digits)
   - `ifsc_code` (11-character RBI standard regex: `^[A-Z]{4}0[A-Z0-9]{6}$`)
   - `bank_name` (auto-resolved from IFSC 4-char prefix on write)
2. **Masked Presentation**:
   - Account numbers are masked on all read endpoints, displaying only terminal 4 digits (e.g., `••••••••4589`).
3. **Self-Healing Payout Release**:
   - If a creator has monthly statements on hold (`status == "pending_bank_details"`), saving a valid bank profile automatically transitions them to `"reconciled"`.

---

## 5. Minimum Payout Threshold Rollovers

* **Threshold**: `MIN_PAYOUT_THRESHOLD = 500.0` (₹500 INR).
* **Rollover Rule**: If a creator's net earnings for a closed calendar month are $< ₹500$, the statement remains in `"accruing"` and automatically rolls forward until cumulative earnings reach the payout threshold.

---

## 6. Back-Office Monthly Reconciliation CLI Workflow

Platform administrators reconcile monthly advertising revenue using the standalone CLI utility:

```bash
# 1. Reconcile by total Google Ad Manager revenue:
python -m app.scripts.reconcile_monthly_ads --month 2026-09 --revenue 75000.0

# 2. Reconcile by fixed eCPM rate:
python -m app.scripts.reconcile_monthly_ads --month 2026-09 --ecpm 180.0

# 3. Confirm wire transfer with official bank UTR:
python -m app.scripts.reconcile_monthly_ads --mark-paid STMT-202609-ADM42-8F9B --utr HDFC20261028994820

# 4. View platform profit ledger:
python -m app.scripts.reconcile_monthly_ads --history
```

### Statement ID Invariants (`1 Transaction ➔ 1 Creator`)
* Every statement ID follows: `STMT-{YYYYMM}-ADM{creator_id}-{hex}`.
* In the database, `UNIQUE(creator_id, month)` prevents duplicate statements.
* Marking a statement paid links the official bank UTR code 1:1 to that creator's statement.

---

## 7. Environment Configuration Reference

| Environment Variable | Type | Default | Purpose |
| :--- | :---: | :---: | :--- |
| `GOOGLE_IMA_VAST_TAG_URL` | `str` | `""` | Base Google IMA VAST ad tag URL with player parameters. |
| `PLATFORM_AD_COMMISSION_PERCENT` | `float` | `30.0` | Platform technology commission retained from gross ad revenue. |
| `PAYOUT_DAY_OF_MONTH` | `int` | `28` | Day of the following month when creator wire disbursements occur. |
| `MIN_PAYOUT_THRESHOLD` | `float` | `500.0` | Minimum net earnings (₹) required to trigger a disbursement. |
| `AD_IMPRESSION_DEBOUNCE_SECONDS` | `int` | `10` | Rapid-fire anti-spam debounce window between consecutive ad pings. |
| `AD_IMPRESSION_SESSION_WINDOW_MINUTES` | `int` | `30` | Rolling session window duration for client frequency rate-limiting. |
| `AD_IMPRESSION_MAX_PER_SESSION` | `int` | `10` | Maximum ad impressions permitted per user per video in the window. |
