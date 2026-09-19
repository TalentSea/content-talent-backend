from fastapi import APIRouter, Query, status

from app.dependencies import CurrentAdmin
from app.schemas.admin.monetization_schemas import (
    MonetizationAnalyticsResponse,
    MonetizationSummaryResponse,
    PayoutProfileResponse,
    PayoutProfileUpdateRequest,
    SettlementsListResponse,
)
from app.services.admin.monetization_service import MonetizationService

router = APIRouter(
    prefix="/api/v1/admin/monetization",
    tags=["Admin Ad Monetization & Settlements"],
)
monetization_service = MonetizationService()


@router.get(
    "/summary",
    response_model=MonetizationSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Creator Earnings & Ad Performance KPI Cards",
    description="Retrieves live estimated ad earnings for the running month, pending payouts, last payout with Bank UTR, and cumulative lifetime earnings.",
)
def get_monetization_summary(
    current_user: CurrentAdmin,
):
    """
    GET /api/v1/admin/monetization/summary
    """
    return monetization_service.get_monetization_summary(
        creator_id=current_user["user_id"]
    )


@router.get(
    "/analytics",
    response_model=MonetizationAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Time-Series Monetization Performance Chart",
    description="Provides granular date-filtered time-series data to render interactive revenue and impression charts in the Creator Studio.",
)
def get_monetization_analytics(
    current_user: CurrentAdmin,
    range: str | None = Query(
        "30d", description="Quick preset window: '7d', '30d', '90d', '6m', '12m'"
    ),
    start_date: str | None = Query(
        None, description="Custom start date (format: YYYY-MM-DD)"
    ),
    end_date: str | None = Query(
        None, description="Custom end date (format: YYYY-MM-DD)"
    ),
    interval: str | None = Query(
        None, description="Granular interval bucket: 'day', 'week', 'month'"
    ),
):
    """
    GET /api/v1/admin/monetization/analytics
    """
    return monetization_service.get_monetization_analytics(
        creator_id=current_user["user_id"],
        range_preset=range,
        start_date_str=start_date,
        end_date_str=end_date,
        interval=interval,
    )


@router.get(
    "/settlements",
    response_model=SettlementsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Monthly Payout Statements & UTR Ledger",
    description="Returns a paginated historical ledger of itemized monthly settlement statements, payment confirmation timestamps, and bank transfer UTR references.",
)
def get_settlements(
    current_user: CurrentAdmin,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(12, ge=1, le=100, description="Items per page"),
):
    """
    GET /api/v1/admin/monetization/settlements
    """
    return monetization_service.get_settlement_history(
        creator_id=current_user["user_id"],
        page=page,
        limit=limit,
    )


@router.get(
    "/settings",
    response_model=PayoutProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Creator Bank Payout Profile",
    description="Retrieves the creator's registered bank account details (with masked account number) for monthly revenue disbursements.",
)
def get_payout_settings(
    current_user: CurrentAdmin,
):
    """
    GET /api/v1/admin/monetization/settings
    """
    return monetization_service.get_payout_profile(creator_id=current_user["user_id"])


@router.put(
    "/settings",
    response_model=PayoutProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Register / Update Creator Bank Payout Profile",
    description="Registers or updates the creator's bank account details. Bank name is auto-resolved from IFSC and persisted.",
)
def update_payout_settings(
    current_user: CurrentAdmin,
    payload: PayoutProfileUpdateRequest,
):
    """
    PUT /api/v1/admin/monetization/settings
    """
    return monetization_service.update_payout_profile(
        creator_id=current_user["user_id"],
        request=payload,
    )
