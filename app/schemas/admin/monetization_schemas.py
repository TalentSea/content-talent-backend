from datetime import datetime

from pydantic import BaseModel, Field

from app.config import get_settings

# ---------------------------------------------------------------------------
# API 1: /summary Schemas
# ---------------------------------------------------------------------------


class CurrentPeriodSummary(BaseModel):
    """Real-time active month metrics with dynamic eCPM resolution."""

    period: str = Field(..., description="Active calendar month (YYYY-MM)")
    estimated_earnings: float | None = Field(
        None, description="Estimated net earnings accrued; null for brand-new creators"
    )
    impressions: int = Field(..., description="Verified ad impressions served so far")
    ecpm: float | None = Field(
        None,
        description="Net eCPM rate; null for brand-new creators until first settlement",
    )
    expected_payout_date: str = Field(
        ...,
        description="Scheduled disbursement date for this month's earnings (YYYY-MM-DD)",
    )


class PendingPayoutSummary(BaseModel):
    """Previous closed month statement awaiting bank disbursement."""

    period: str = Field(..., description="Closed billing cycle (YYYY-MM)")
    amount: float = Field(..., description="Reconciled net payout amount")
    status: str = Field(
        ..., description="Settlement state: 'reconciled' or 'pending_bank_details'"
    )
    payout_date: str = Field(
        ..., description="Scheduled disbursement date (YYYY-MM-DD, e.g. 28th)"
    )


class LastPayoutSummary(BaseModel):
    """Latest successfully completed bank disbursement with official UTR reference."""

    period: str = Field(..., description="Billing cycle of the last payout (YYYY-MM)")
    amount: float = Field(..., description="Disbursed payout amount")
    payout_date: str = Field(..., description="Date transferred to bank (YYYY-MM-DD)")
    utr: str | None = Field(
        None, description="Official bank transaction reference number (UTR)"
    )


class MonetizationSummaryResponse(BaseModel):
    """Response DTO for GET /api/v1/admin/monetization/summary."""

    currency: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CURRENCY,
        description="Three-letter currency code",
    )
    payout_profile_configured: bool = Field(
        default=False,
        description="True if creator has registered a valid bank account for payouts",
    )
    current_period: CurrentPeriodSummary
    pending_payout: PendingPayoutSummary | None = None
    last_payout: LastPayoutSummary | None = None
    lifetime_earnings: float = Field(
        default=0.0, description="Cumulative sum of all settled disbursements"
    )


# ---------------------------------------------------------------------------
# API 2: /analytics Schemas
# ---------------------------------------------------------------------------


class MonetizationAnalyticsPoint(BaseModel):
    """Time-series data point for interactive ad earnings and impression charts."""

    date: str = Field(..., description="ISO boundary date (YYYY-MM-DD)")
    impressions: int = Field(..., description="Verified ad impressions served")
    ecpm: float | None = Field(
        None, description="Net eCPM rate; null for new creators without history"
    )
    estimated_earnings: float | None = Field(
        None,
        description="Estimated net earnings; null for new creators without history",
    )


class MonetizationAnalyticsResponse(BaseModel):
    """Response DTO for GET /api/v1/admin/monetization/analytics."""

    start_date: str = Field(..., description="Resolved ISO start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Resolved ISO end date (YYYY-MM-DD)")
    interval: str = Field(..., description="Bucket interval: 'day', 'week', or 'month'")
    currency: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CURRENCY,
        description="Three-letter currency code",
    )
    data_points: list[MonetizationAnalyticsPoint] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API 3: /settlements Schemas
# ---------------------------------------------------------------------------


class SettlementItemResponse(BaseModel):
    """Itemized monthly statement and UTR bank ledger record."""

    statement_id: str = Field(..., description="Unique business statement identifier")
    month: str = Field(..., description="Billing cycle month (YYYY-MM)")
    impressions_count: int = Field(..., description="Verified billable ad impressions")
    ecpm: float = Field(..., description="Net creator eCPM rate applied")
    amount: float = Field(..., description="Net payout amount transferred to bank")
    currency: str = Field(
        default_factory=lambda: get_settings().DEFAULT_CURRENCY,
        description="Three-letter currency code",
    )
    status: str = Field(
        ...,
        description="Settlement state: 'accruing', 'pending_bank_details', 'reconciled', 'paid'",
    )
    settled_at: datetime | None = Field(
        None, description="Timestamp when bank transfer completed"
    )
    transaction_reference: str | None = Field(
        None, description="Official Bank UTR reference number"
    )
    invoice_url: str | None = Field(
        None, description="Secure link to downloadable PDF statement"
    )


class SettlementsListResponse(BaseModel):
    """Paginated response DTO for GET /api/v1/admin/monetization/settlements."""

    items: list[SettlementItemResponse] = Field(default_factory=list)
    total: int = Field(..., description="Total settlement records across all pages")
    page: int = Field(..., description="Current active page number")
    limit: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total available pages")


# ---------------------------------------------------------------------------
# API 4 & 5: /settings Schemas (Bank Payout Profile)
# ---------------------------------------------------------------------------


class PayoutProfileResponse(BaseModel):
    """Response DTO for GET /api/v1/admin/monetization/settings."""

    account_holder_name: str | None = Field(
        None, description="Name as registered with the bank"
    )
    bank_name: str | None = Field(
        None, description="Official bank name auto-resolved from IFSC"
    )
    account_number_masked: str | None = Field(
        None, description="Masked bank account number (••••••••4589)"
    )
    ifsc_code: str | None = Field(
        None, description="Indian Financial System Code (11 alphanumeric)"
    )
    updated_at: datetime | None = Field(
        None, description="Timestamp when bank details were last updated"
    )


class PayoutProfileUpdateRequest(BaseModel):
    """Request DTO for PUT /api/v1/admin/monetization/settings."""

    account_holder_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Official account holder name registered with the bank",
    )
    account_number: str = Field(
        ...,
        min_length=9,
        max_length=18,
        description="Full bank account number (digits only)",
    )
    ifsc_code: str = Field(
        ...,
        pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$",
        description="11-character Indian Financial System Code (e.g. HDFC0000128)",
    )
