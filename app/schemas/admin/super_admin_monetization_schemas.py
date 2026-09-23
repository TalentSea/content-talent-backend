from datetime import datetime

from pydantic import BaseModel, Field

from app.config import get_settings
from app.schemas.shared.common_schemas import PaginatedResponse

# ---------------------------------------------------------------------------
# API 1 & 2: Generate Draft & Publish Reconciliations
# ---------------------------------------------------------------------------


class DraftReconciliationRequest(BaseModel):
    """Request DTO for POST /api/v1/admin/monetization/reconciliations"""

    month: str = Field(
        ..., pattern=r"^\d{4}-\d{2}$", description="Billing cycle (YYYY-MM)"
    )
    gross_revenue: float = Field(
        ..., gt=0, description="Total Google Ad Manager revenue"
    )
    notes: str | None = Field(
        None, description="Optional admin notes for this billing cycle"
    )


class TenantStatementDraft(BaseModel):
    """Nested payload for individual tenant payout calculation preview during draft phase."""

    tenant_id: int
    tenant_name: str
    impressions_count: int
    net_ecpm: float
    net_amount: float
    gross_revenue: float
    platform_fee: float


class TenantStatementPublished(BaseModel):
    """Nested payload for finalized individual tenant statements."""

    tenant_id: int
    tenant_name: str
    statement_id: str
    impressions_count: int
    net_ecpm: float
    net_amount: float
    gross_revenue: float
    platform_fee: float
    status: str
    scheduled_payout_date: str | None = Field(
        None, description="Scheduled transfer date (YYYY-MM-DD)"
    )


class PlatformReconciliationResponse(BaseModel):
    """Response DTO for generating drafts."""

    id: int
    month: str
    total_google_revenue: float
    total_impressions: int
    gross_ecpm: float
    platform_commission_pct: float
    platform_profit: float
    creator_pool_amount: float
    creator_net_ecpm: float
    creators_count: int
    currency: str = Field(default_factory=lambda: get_settings().DEFAULT_CURRENCY)
    status: str
    notes: str | None
    statements: list[TenantStatementDraft] = Field(default_factory=list)


class PublishReconciliationResponse(BaseModel):
    """Response DTO for publishing finalized reconciliations (API 2)."""

    id: int
    month: str
    total_google_revenue: float
    status: str
    currency: str = Field(default_factory=lambda: get_settings().DEFAULT_CURRENCY)
    creator_pool_amount: float
    platform_profit: float
    reconciled_at: datetime
    statements: list[TenantStatementPublished] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API 3: Mark Paid
# ---------------------------------------------------------------------------


class MarkPaidRequest(BaseModel):
    """Request DTO for POST /api/v1/admin/monetization/settlements/{statement_id}/mark-paid"""

    transaction_reference: str = Field(..., description="Official Bank UTR code")
    invoice_url: str | None = Field(None, description="Link to PDF invoice/receipt")


class SettledStatementResponse(BaseModel):
    """Response DTO for successfully marking a statement as paid."""

    statement_id: str
    tenant_id: int
    month: str
    amount: float
    currency: str = Field(default_factory=lambda: get_settings().DEFAULT_CURRENCY)
    status: str
    transaction_reference: str
    settled_at: datetime


# ---------------------------------------------------------------------------
# API 4: Audit Ledger
# ---------------------------------------------------------------------------


class ReconciliationListItem(BaseModel):
    """Summary item for the Audit Ledger."""

    id: int
    month: str
    total_google_revenue: float
    platform_profit: float
    creator_pool_amount: float
    currency: str = Field(default_factory=lambda: get_settings().DEFAULT_CURRENCY)
    status: str
    reconciled_at: datetime | None = None


class ReconciliationListResponse(PaginatedResponse[ReconciliationListItem]):
    """Response DTO for GET /api/v1/admin/monetization/reconciliations"""
