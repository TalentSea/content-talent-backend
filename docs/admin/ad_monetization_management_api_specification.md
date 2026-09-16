# Creator Admin Ad Monetization & Monthly Revenue Settlement API Specification

This specification defines the dedicated **Creator Ad Monetization Management & Settlement Endpoints** (`/api/v1/admin/monetization/*`) for the Creator Admin Studio Web Portal.

---

## 🏛️ Centralized Platform Monetization & Settlement Architecture

In this enterprise white-labeled OTT model, all white-labeled mobile applications stream ads served through the **TalentSea Master Google Ad Manager (GAM) / VAST Network**. Creators do not need to manage individual Google publisher accounts, undergo complex domain verifications, or configure ad tags.

```
                      [Mobile App (Standard Tier Subscriber)]
                                         │
                                         │ 1. Streams video with platform VAST tag
                                         │    (&cust_params=creator_id=101&video_id=202)
                                         ▼
                      [Google IMA SDK renders video ad]
                                         │
                                         │ 2. Telemetry beacon (HTTP 204)
                                         │    POST /api/v1/mobile/videos/{id}/ad-impression
                                         ▼
                      [Backend Engine: ad_impression_events]
                                         │
                                         │ 3. Aggregates impressions & calculates eCPM earnings
                                         ▼
             ┌────────────────────────────────────────────────────────┐
             │            Creator Studio Web Portal                   │
             │                                                        │
             │  • GET /api/v1/admin/monetization/summary              │
             │    (Real-time live estimated earnings & KPI cards)     │
             │                                                        │
             │  • GET /api/v1/admin/monetization/analytics            │
             │    (Interactive daily impressions & revenue chart)     │
             │                                                        │
             │  • GET /api/v1/admin/monetization/settlements          │
             │    (Itemized monthly payout statements & UTR ledger)   │
             │                                                        │
             │  • GET/PUT /api/v1/admin/monetization/settings         │
             │    (Master ad toggle & bank payout account profile)    │
             └────────────────────────────────────────────────────────┘
```

### Key Business Architecture Pillars:

1. **Dynamic Creator Attribution (`cust_params`):**
   - When the mobile app requests video playback details via `GET /api/v1/mobile/videos/{id}`, the backend dynamically appends creator and video identifiers to the platform VAST tag:
     ```text
     {settings.GOOGLE_IMA_VAST_TAG_URL}&cust_params=creator_id%3D{video.user_id}%26video_id%3D{video.id}
     ```
   - Google Ad Manager logs ad impressions against the specific creator's inventory, allowing reconciliation against Google's monthly publisher reports.
2. **Discreet White-Label Monetization & eCPM Commission Deduction:**
   - **Commission is Taken Directly from the eCPM Layer:**
     Instead of showing a fee deduction on the creator's payout statement, the platform applies its commission directly to the eCPM:
     $$\text{Creator eCPM} = \text{Raw Google eCPM} \times \left(1 - \frac{\text{PLATFORM\_AD\_COMMISSION\_PERCENT}}{100}\right)$$
   - **Centralized Configuration:**
     ```env
     PLATFORM_AD_COMMISSION_PERCENT=30.0
     ```
   - **How the Money & Math Work:**
     - **Raw Google Rate:** Google generates gross eCPM of `₹180.00` per 1,000 impressions.
     - **Platform Commission (30%):** Backend applies $(1 - 0.30)$ to yield **`Creator eCPM = ₹126.00`**.
     - **For 380,450 verified ad impressions:**
       $$\text{Creator Earnings} = \frac{380,450 \times ₹126.00}{1000} = \mathbf{₹47,936.70}$$
     - **Bank Execution:**
       - Google deposits gross revenue **₹68,481.00** into TalentSea's master bank account.
       - TalentSea retains its 30% technology fee (**₹20,544.30**).
       - TalentSea transfers **₹47,936.70** to the creator's bank account with Bank UTR.
   - **Why This Protects the White-Label Brand:**
     - The creator sees: `Impressions: 380,450`, `eCPM: ₹126.00`, `Payout Amount: ₹47,936.70`.
     - The formula $\frac{\text{Impressions} \times \text{eCPM}}{1000} = \text{Payout}$ calculates with 100% mathematical precision.
     - The creator sees zero platform cuts, fees, or deductions, believing they received 100% of their ad earnings.
3. **Monthly Settlement Lifecycle & Payout Date Resolution (Net-30 Schedule):**

   ### Why This Month's Payout Reflects Previous Month's Ad Views:

   In digital ad networks (Google Ad Manager, AdSense, programmatic VAST exchanges), ad revenue cannot be paid instantly on the day ads are viewed. The industry standard **Net-30 settlement cycle** operates as follows:
   - **Auditing & Fraud Scrubbing:** Google runs automated fraud detection throughout the month to identify and eliminate accidental clicks, spam bots, and invalid traffic (IVT) before finalizing gross billings.
   - **Advertiser Remittance:** Brand advertisers pay Google on 30-day corporate terms. Google then consolidates and disburses net publisher revenues between the **21st and 25th of the following month**.
   - **Platform Verification & Creator Transfer:** TalentSea verifies incoming funds and initiates creator bank disbursements on the **28th of the following month**.

   Therefore, **any payout received in October pays for ad views served between September 1st and September 30th**.

   ```
   [ Month 1: September 1 - 30 ]           [ Month 2: October 1 - 20 ]         [ Month 2: October 21 - 25 ]      [ Month 2: October 28 ]
   ┌───────────────────────────┐           ┌─────────────────────────┐         ┌──────────────────────────┐      ┌──────────────────────────┐
   │ Viewers stream videos.    │           │ September month closes. │         │ Google Ad Manager audits │      │ TalentSea initiates bank │
   │ Ad impressions log live.  │ ────────> │ Impressions locked.     │ ──────> │ & disburses net funds to │ ───> │ transfers (NEFT/RTGS) to │
   │ Est. earnings accumulate. │           │ Settlement generated:   │         │ platform master account. │      │ creator bank accounts.   │
   │ Status: "accruing"        │           │ Status: "reconciled"    │         │                          │      │ Status: "paid" + UTR     │
   └───────────────────────────┘           └─────────────────────────┘         └──────────────────────────┘      └──────────────────────────┘
   ```

   ### The Four Lifecycle Stages:
   - **Stage 1 — Accrual Window (1st – End of Month):**
     - Active month (`current_period`).
     - Real-time counter of verified ad impressions and estimated earnings.
     - `"expected_payout_date"` projects when this running month will be paid (e.g. `2026-11-28` for October).
   - **Stage 2 — Reconciliation Window (1st – 20th of Following Month):**
     - When the month closes, it transitions to `pending_payout`.
     - Impressions and gross revenues are locked and cross-checked against Google publisher telemetry.
     - State is marked `"reconciled"`.
   - **Stage 3 — Settlement Window (21st – 25th of Following Month):**
     - Google Ad Manager remits cleared funds to the platform bank account.
     - Platform prepares batch bank disbursement files (Razorpay Payouts / ICICI / HDFC Corporate Banking).
   - **Stage 4 — Creator Disbursement Window (26th – 28th of Following Month):**
     - Automated payouts execute on the configured **`PAYOUT_DAY_OF_MONTH`** (28th).
     - Bank returns a unique transaction reference (**UTR**).
     - The record is marked `"paid"` and moves to `last_payout`. `pending_payout` resets to `null` until the next cycle closes.

   ### Centralized Configuration (Zero Hardcoding):
   - The payout day is defined in `.env` and `app/config.py` (`PAYOUT_DAY_OF_MONTH=28`).
   - **Why Day 28?**
     1. It provides a reliable 2–3 business day clearance window following Google's deposit (21st–25th).
     2. Day 28 is universally present across all 12 calendar months (including February in standard 28-day years), preventing date overflow errors.

---

## 🛡️ Security & RBAC Rules Matrix

All endpoints in this subsystem strictly require an authenticated Creator Admin session:

| Endpoint                                 | Method | Guard                        |  Allowed Roles   | Description                                          |
| :--------------------------------------- | :----: | :--------------------------- | :--------------: | :--------------------------------------------------- |
| `/api/v1/admin/monetization/summary`     | `GET`  | `Depends(get_current_admin)` | Strictly `admin` | Real-time earnings KPIs & current month overview     |
| `/api/v1/admin/monetization/analytics`   | `GET`  | `Depends(get_current_admin)` | Strictly `admin` | Time-series chart data (impressions, eCPM, earnings) |
| `/api/v1/admin/monetization/settlements` | `GET`  | `Depends(get_current_admin)` | Strictly `admin` | Paginated monthly payout statements & UTR ledger     |
| `/api/v1/admin/monetization/settings`    | `GET`  | `Depends(get_current_admin)` | Strictly `admin` | Fetches creator bank payout profile                  |
| `/api/v1/admin/monetization/settings`    | `PUT`  | `Depends(get_current_admin)` | Strictly `admin` | Registers or updates creator bank payout details     |

---

## 🔌 API Endpoints Specification

### 1. `GET /api/v1/admin/monetization/summary` — Creator Earnings & Ad Performance KPI Cards

Retrieves high-level summary metrics for the Creator Admin Studio dashboard cards.

#### Request Headers

```http
Authorization: Bearer <creator_access_token>
```

#### Response Specification (`200 OK`)

```json
{
  "currency": "INR",
  "current_period": {
    "period": "2026-10",
    "estimated_earnings": 1420.5,
    "impressions": 11200,
    "ecpm": 126.83,
    "expected_payout_date": "2026-11-28"
  },
  "pending_payout": {
    "period": "2026-09",
    "amount": 23957.32,
    "status": "reconciled",
    "payout_date": "2026-10-28"
  },
  "last_payout": {
    "period": "2026-08",
    "amount": 21400.0,
    "payout_date": "2026-08-28",
    "utr": "HDFC00098765432"
  },
  "lifetime_earnings": 142850.0
}
```

> **Lifecycle Note on Payouts & Month Offset:**
>
> - In this model, **payouts disbursed in month $M$ always pay for month $M-1$'s verified ad views** (Net-30 cycle).
> - **Concrete October 2026 Example:**
>   - `"current_period"`: Shows **October 1–31** ad impressions accumulating in real time. Its `"expected_payout_date"` is **`2026-11-28`**.
>   - `"pending_payout"`: Holds the finalized earnings for **September 1–30** ad views. Scheduled for bank transfer on **`2026-10-28`**. Once paid, this becomes `null`.
>   - `"last_payout"`: Displays the completed transfer for **August 1–31** ad views, paid with Bank UTR reference.
>   - If a new creator has not received any payouts yet, `"last_payout"` will be `null`.

#### Response Fields

| Field                                 |       Type       | Description                                                                                                |
| :------------------------------------ | :--------------: | :--------------------------------------------------------------------------------------------------------- |
| `currency`                            |     `string`     | Top-level 3-letter currency code (e.g. `"INR"`).                                                           |
| `current_period.period`               |     `string`     | Active live calendar month formatted as `YYYY-MM`.                                                         |
| `current_period.estimated_earnings`   |     `float`      | Estimated net take-home earnings accrued so far in the active month.                                       |
| `current_period.impressions`          |    `integer`     | Total verified video ad impressions served in the active month.                                            |
| `current_period.ecpm`                 |     `float`      | Effective Cost Per Mille (net earnings per 1,000 ad impressions).                                          |
| `current_period.expected_payout_date` |     `string`     | Projected date when this active month's balance will be disbursed (`YYYY-MM-DD`, e.g. 28th of next month). |
| `pending_payout`                      | `object \| null` | Previous closed month's finalized earnings awaiting bank transfer (or `null` if none pending).             |
| `pending_payout.period`               |     `string`     | Closed month cycle awaiting payout (`YYYY-MM`).                                                            |
| `pending_payout.amount`               |     `float`      | Final reconciled amount to be disbursed.                                                                   |
| `pending_payout.status`               |     `string`     | Settlement state: `"reconciled"` (locked and ready for transfer).                                          |
| `pending_payout.payout_date`          |     `string`     | Scheduled disbursement transfer date (`YYYY-MM-DD`).                                                       |
| `last_payout`                         | `object \| null` | Most recent successful monthly payout details (or `null` if no prior payouts).                             |
| `last_payout.period`                  |     `string`     | Billing cycle of the last payout (`YYYY-MM`).                                                              |
| `last_payout.amount`                  |     `float`      | Disbursed payout amount.                                                                                   |
| `last_payout.payout_date`             |     `string`     | Date payout was transferred to bank account (`YYYY-MM-DD`).                                                |
| `last_payout.utr`                     |     `string`     | Official bank transaction reference number (UTR).                                                          |
| `lifetime_earnings`                   |     `float`      | Cumulative total of all settled earnings disbursed since account creation.                                 |

---

### 2. `GET /api/v1/admin/monetization/analytics` — Time-Series Performance Chart

Provides granular date-filtered time-series data to render interactive revenue and impression charts in the Creator Studio. Fully mirrors the query structure and envelope format of `GET /api/v1/admin/dashboard/analytics`.

#### Request Headers

```http
Authorization: Bearer <creator_access_token>
```

#### Query Parameters

| Parameter    |      Type       | Required |     Default     | Description                                                                |
| :----------- | :-------------: | :------: | :-------------: | :------------------------------------------------------------------------- |
| `range`      |    `string`     |    No    |     `"30d"`     | Quick preset selection window (`"7d"`, `"30d"`, `"90d"`, `"6m"`, `"12m"`). |
| `start_date` | `string` (date) |    No    | Auto from range | Custom start date (`YYYY-MM-DD`).                                          |
| `end_date`   | `string` (date) |    No    | Auto from range | Custom end date (`YYYY-MM-DD`).                                            |
| `interval`   |    `string`     |    No    |  Auto-resolved  | Date grouping frequency: `"day"`, `"week"`, or `"month"`.                  |

##### Interval Auto-Resolution Matrix (When `interval` is omitted):

| Total Duration ($D = \text{end} - \text{start}$) | Auto-Selected `interval` | Typical Points  |
| :----------------------------------------------- | :----------------------: | :-------------: |
| $D \le 30\text{ days}$ (e.g. `7d`, `30d`)        |         `"day"`          | 7 to 30 points  |
| $31 \le D \le 90\text{ days}$ (e.g. `90d`)       |         `"week"`         | ~8 to 13 points |
| $D \ge 91\text{ days}$ (e.g. `6m`, `12m`)        |        `"month"`         | 6 to 12 points  |

#### Response Specification (`200 OK`)

```json
{
  "start_date": "2026-09-01",
  "end_date": "2026-09-16",
  "interval": "day",
  "currency": "INR",
  "data_points": [
    {
      "date": "2026-09-14",
      "impressions": 11840,
      "ecpm": 127.4,
      "estimated_earnings": 1508.41
    },
    {
      "date": "2026-09-15",
      "impressions": 12450,
      "ecpm": 131.6,
      "estimated_earnings": 1638.42
    },
    {
      "date": "2026-09-16",
      "impressions": 14120,
      "ecpm": 129.15,
      "estimated_earnings": 1823.58
    }
  ]
}
```

#### Response Fields

| Field                              |   Type    | Description                                                                       |
| :--------------------------------- | :-------: | :-------------------------------------------------------------------------------- |
| `start_date`                       | `string`  | Resolved ISO start date (`YYYY-MM-DD`).                                           |
| `end_date`                         | `string`  | Resolved ISO end date (`YYYY-MM-DD`).                                             |
| `interval`                         | `string`  | Grouping bucket applied: `"day"`, `"week"`, or `"month"`.                         |
| `currency`                         | `string`  | Three-letter currency code (e.g. `"INR"`).                                        |
| `data_points`                      |  `array`  | Ordered chronological array of bucketed time points.                              |
| `data_points[].date`               | `string`  | ISO boundary date (`YYYY-MM-DD`) for machine sorting, chart x-axis, and tooltips. |
| `data_points[].impressions`        | `integer` | Total verified video ad impressions served in the interval bucket.                |
| `data_points[].ecpm`               |  `float`  | Effective CPM (revenue per 1,000 impressions) for the interval bucket.            |
| `data_points[].estimated_earnings` |  `float`  | Creator's net 70% take-home earnings accrued in the interval bucket.              |

---

### 3. `GET /api/v1/admin/monetization/settlements` — Monthly Payout Statements & UTR Ledger

Returns a paginated historical ledger of itemized monthly settlement statements, payment confirmation timestamps, and bank transfer UTR references.

#### Request Headers

```http
Authorization: Bearer <creator_access_token>
```

#### Query Parameters

| Parameter |   Type    | Required | Default | Description                         |
| :-------- | :-------: | :------: | :-----: | :---------------------------------- |
| `page`    | `integer` |    No    |   `1`   | Page number for pagination          |
| `limit`   | `integer` |    No    |  `12`   | Items per page (default: 12 months) |

#### Response Specification (`200 OK`)

```json
{
  "items": [
    {
      "statement_id": "STMT-2026-08-101",
      "month": "2026-08",
      "impressions_count": 380450,
      "ecpm": 126.0,
      "amount": 47936.7,
      "currency": "INR",
      "status": "paid",
      "settled_at": "2026-09-28T11:30:00Z",
      "transaction_reference": "UTR_RAZORPAY_881923841",
      "invoice_url": "https://talentsea.b-cdn.net/statements/stmt_2026_08_101.pdf"
    },
    {
      "statement_id": "STMT-2026-07-101",
      "month": "2026-07",
      "impressions_count": 310200,
      "ecpm": 122.5,
      "amount": 37999.5,
      "currency": "INR",
      "status": "paid",
      "settled_at": "2026-08-28T14:15:00Z",
      "transaction_reference": "UTR_RAZORPAY_773619284",
      "invoice_url": "https://talentsea.b-cdn.net/statements/stmt_2026_07_101.pdf"
    }
  ],
  "total": 2,
  "page": 1,
  "limit": 12,
  "total_pages": 1
}
```

#### Response Fields

| Field                           |       Type       | Description                                                                                            |
| :------------------------------ | :--------------: | :----------------------------------------------------------------------------------------------------- |
| `items[].statement_id`          |     `string`     | Unique monthly statement identifier.                                                                   |
| `items[].month`                 |     `string`     | Billing month cycle (`YYYY-MM`).                                                                       |
| `items[].impressions_count`     |    `integer`     | Total verified video ad impressions served in that month.                                              |
| `items[].ecpm`                  |     `float`      | Effective CPM for the month (direct net rate).                                                         |
| `items[].amount`                |     `float`      | Net earnings disbursed to creator bank account ($\frac{\text{impressions} \times \text{ecpm}}{1000}$). |
| `items[].currency`              |     `string`     | Three-letter currency code (e.g. `"INR"`).                                                             |
| `items[].status`                |     `string`     | Settlement state: `"accruing"`, `"reconciled"`, or `"paid"`.                                           |
| `items[].settled_at`            | `string \| null` | ISO timestamp when bank disbursement succeeded (`null` if pending).                                    |
| `items[].transaction_reference` | `string \| null` | Official bank transaction reference (UTR) (`null` if pending).                                         |
| `items[].invoice_url`           | `string \| null` | Secure CDN link to the downloadable PDF statement (`null` if pending).                                 |
| `total`                         |    `integer`     | Total settlement records across all pages.                                                             |
| `page`                          |    `integer`     | Current active page number.                                                                            |
| `limit`                         |    `integer`     | Number of items per page.                                                                              |
| `total_pages`                   |    `integer`     | Total available pages.                                                                                 |

#### Settlement Status Lifecycle:

- `accruing`: Current month in progress. Numbers represent dynamic real-time estimates.
- `reconciled`: Billing period closed and verified against Google Ad Manager master report. Awaiting bank transfer batch.
- `paid`: Payment successfully executed via bank transfer. `transaction_reference` (UTR) and downloadable PDF statement are attached.

---

### 4. `GET /api/v1/admin/monetization/settings` — Retrieve Creator Bank Payout Profile

Retrieves the creator's registered bank account details (with masked account number) for monthly revenue disbursements.

#### Request Headers

```http
Authorization: Bearer <creator_access_token>
```

#### Response Specification (`200 OK`)

```json
{
  "account_holder_name": "Acme Media Studio",
  "bank_name": "HDFC Bank",
  "account_number_masked": "••••••••4589",
  "ifsc_code": "HDFC0000128",
  "updated_at": "2026-09-10T12:00:00Z"
}
```

> If the creator has not yet registered a bank account, all fields will return `null`.

#### Response Fields
| Field | Type | Description |
| :--- | :---: | :--- |
| `account_holder_name` | `string \| null` | Name as registered with the bank. |
| `bank_name` | `string \| null` | Official bank name auto-resolved by backend from the IFSC code. |
| `account_number_masked` | `string \| null` | Masked account number showing only last 4 digits. |
| `ifsc_code` | `string \| null` | Indian Financial System Code. |
| `updated_at` | `string \| null` | ISO timestamp when bank details were last updated. |

---

### 5. `PUT /api/v1/admin/monetization/settings` — Register / Update Creator Bank Payout Profile

Registers or updates the creator's bank account details for receiving monthly ad revenue payouts.

> **Note:** The creator does **not** type the bank name. The backend automatically resolves and persists the official `bank_name` from the validated `ifsc_code`.

#### Request Headers

```http
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

#### Request Body

```json
{
  "account_holder_name": "Acme Media Studio",
  "account_number": "50100234564589",
  "ifsc_code": "HDFC0000128"
}
```

#### Request Payload Validation Rules

- `account_holder_name`: Required string (min 3, max 100 characters).
- `account_number`: Required string (9 to 18 digits).
- `ifsc_code`: Required string (11 characters, matching Indian IFSC format `^[A-Z]{4}0[A-Z0-9]{6}$`).

#### Response Specification (`200 OK`)

```json
{
  "account_holder_name": "Acme Media Studio",
  "bank_name": "HDFC Bank",
  "account_number_masked": "••••••••4589",
  "ifsc_code": "HDFC0000128",
  "updated_at": "2026-09-16T15:00:00Z"
}
```

---

## 💻 Website Frontend Implementation Guide (Creator Studio UI)

The Creator Studio web portal renders a comprehensive **Monetization & Ads** dashboard:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ 💰 In-Stream Video Ad Monetization                                                               │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ ┌───────────────────┐ │
│ │ 📺 Ad Impressions    │ │ 📈 Average eCPM      │ │ 💵 Est. Net Earnings │ │ 🗓 Next Settlement│ │
│ │ 184,500              │ │ ₹185.50              │ │ ₹23,957.32           │ │ Oct 28, 2026      │ │
│ └──────────────────────┘ └──────────────────────┘ └──────────────────────┘ └───────────────────┘ │
│                                                                                                  │
│ 📊 Daily Ad Performance & Earnings Chart (Last 30 Days)                                          │
│ ┌──────────────────────────────────────────────────────────────────────────────────────────────┐ │
│ │  ₹2,000 ┤              ╭────╮                                                                │ │
│ │  ₹1,500 ┤        ╭─────╯    ╰───────╮                                                        │ │
│ │  ₹1,000 ┤  ╭─────╯                  ╰─────────                                               │ │
│ │         └─────────────────────────────────────                                               │ │
│ │           Sep 01         Sep 08         Sep 15                                               │ │
│ └──────────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                                  │
│ 📋 Monthly Settlement Statements & Payout Ledger                                                 │
│ ┌───────────┬─────────────┬──────────────┬──────────────┬──────────┬──────────────┬────────────┐ │
│ │ Month     │ Impressions │ eCPM         │ Payout Amount│ Status   │ UTR Ref      │ Action     │ │
│ ├───────────┼─────────────┼──────────────┼──────────────┼──────────┼──────────────┼────────────┤ │
│ │ Aug 2026  │ 380,450     │ ₹126.00      │ ₹47,936.70   │  PAID    │ UTR_88192384 │ [Download] │ │
│ │ Jul 2026  │ 310,200     │ ₹122.50      │ ₹37,999.50   │  PAID    │ UTR_77361928 │ [Download] │ │
│ └───────────┴─────────────┴──────────────┴──────────────┴──────────┴──────────────┴────────────┘ │
│                                                                                                  │
│ 🏦 Payout Bank Account Details                                                                   │
│ Bank: HDFC Bank  |  Account: ••••••••4589  |  IFSC: HDFC0000128             [ Edit Details ] │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```
