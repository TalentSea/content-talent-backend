from fastapi import APIRouter, Query, status

from app.dependencies import CurrentSuperAdmin
from app.schemas.admin.super_admin_monetization_schemas import (
    DraftReconciliationRequest,
    MarkPaidRequest,
    PlatformReconciliationResponse,
    PublishReconciliationResponse,
    ReconciliationListResponse,
    SettledStatementResponse,
)
from app.services.admin.super_admin_monetization_service import (
    SuperAdminMonetizationService,
)

router = APIRouter(
    prefix="/api/v1/admin/monetization",
    tags=["Super Admin Monetization"],
)
service = SuperAdminMonetizationService()


@router.post(
    "/reconciliations",
    response_model=PlatformReconciliationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Monthly Reconciliation Draft",
)
def generate_reconciliation_draft(
    current_admin: CurrentSuperAdmin,
    request: DraftReconciliationRequest,
):
    """
    API 1: Generates the top-level math and nested statement preview without creating any individual creator statements.
    """
    return service.generate_draft(request)


@router.post(
    "/reconciliations/{month}/publish",
    response_model=PublishReconciliationResponse,
    status_code=status.HTTP_200_OK,
    summary="Publish Reconciliation (Generate Statements)",
)
def publish_reconciliation(
    current_admin: CurrentSuperAdmin,
    month: str,
):
    """
    API 2: Locks the draft, officially transitions the status to "reconciled", and generates all statements.
    """
    return service.publish_reconciliation(month=month)


@router.post(
    "/settlements/{statement_id}/mark-paid",
    response_model=SettledStatementResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm Bank Wire Transfer (Mark Statement Paid with UTR)",
)
def mark_statement_paid(
    current_admin: CurrentSuperAdmin,
    statement_id: str,
    request: MarkPaidRequest,
):
    """
    API 3: After executing bank transfers on the 28th, the Super Admin submits the official Bank UTR code.
    """
    return service.mark_statement_paid(statement_id=statement_id, request=request)


@router.get(
    "/reconciliations",
    response_model=ReconciliationListResponse,
    status_code=status.HTTP_200_OK,
    summary="Master Platform Financial History & Audit Ledger",
)
def list_reconciliations(
    current_admin: CurrentSuperAdmin,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(12, ge=1, le=100, description="Items per page"),
):
    """
    API 4: Retrieves the paginated list of all platform-wide reconciliations (drafts and disbursed).
    """
    return service.get_audit_ledger(page=page, limit=limit)
