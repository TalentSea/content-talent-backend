from fastapi import HTTPException, status

from app.config import get_settings
from app.repositories.admin.super_admin_monetization_repository import (
    SuperAdminMonetizationRepository,
)
from app.schemas.admin.super_admin_monetization_schemas import (
    DraftReconciliationRequest,
    MarkPaidRequest,
    PlatformReconciliationResponse,
    PublishReconciliationResponse,
    ReconciliationListItem,
    ReconciliationListResponse,
    SettledStatementResponse,
    TenantStatementPublished,
)


class SuperAdminMonetizationService:
    """
    Service layer orchestrating the business logic for Super Admin
    Monetization operations, bridging DTOs and the repository.
    """

    def __init__(self):
        self.repository = SuperAdminMonetizationRepository()

    def generate_draft(
        self, request: DraftReconciliationRequest
    ) -> PlatformReconciliationResponse:
        """
        Calculates the draft platform reconciliation and individual tenant statements.
        """
        # Fetch the platform margin percentage dynamically from configuration
        platform_commission_pct = get_settings().PLATFORM_AD_COMMISSION_PERCENT

        try:
            platform_draft, preview_statements = self.repository.generate_draft(
                month=request.month,
                gross_revenue=request.gross_revenue,
                notes=request.notes,
                platform_commission_pct=platform_commission_pct,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )

        return PlatformReconciliationResponse(
            id=platform_draft.id,
            month=platform_draft.month,
            total_google_revenue=float(platform_draft.total_google_revenue),
            total_impressions=platform_draft.total_impressions,
            gross_ecpm=float(platform_draft.gross_ecpm),
            platform_commission_pct=float(platform_draft.platform_commission_pct),
            platform_profit=float(platform_draft.platform_profit),
            creator_pool_amount=float(platform_draft.creator_pool_amount),
            creator_net_ecpm=float(platform_draft.creator_net_ecpm),
            creators_count=platform_draft.creators_count,
            currency=platform_draft.currency,
            status=platform_draft.status,
            notes=platform_draft.notes,
            statements=preview_statements,
        )

    def publish_reconciliation(self, month: str) -> PublishReconciliationResponse:
        """
        Locks the draft platform reconciliation and publishes the official statements.
        """
        try:
            platform_reconciliation, generated_statements = (
                self.repository.publish_reconciliation(month=month)
            )
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        statement_dtos = []
        for stmt in generated_statements:
            statement_dtos.append(
                TenantStatementPublished(
                    tenant_id=stmt.tenant_id,
                    tenant_name=stmt.tenant.name,
                    statement_id=stmt.statement_id,
                    impressions_count=stmt.impressions_count,
                    net_ecpm=float(stmt.ecpm),
                    net_amount=float(stmt.amount),
                    gross_revenue=float(stmt.gross_revenue),
                    platform_fee=float(stmt.platform_fee),
                    status=stmt.status,
                    scheduled_payout_date=stmt.scheduled_payout_date.strftime(
                        "%Y-%m-%d"
                    )
                    if stmt.scheduled_payout_date
                    else None,
                )
            )

        return PublishReconciliationResponse(
            id=platform_reconciliation.id,
            month=platform_reconciliation.month,
            total_google_revenue=float(platform_reconciliation.total_google_revenue),
            status=platform_reconciliation.status,
            currency=platform_reconciliation.currency,
            creator_pool_amount=float(platform_reconciliation.creator_pool_amount),
            platform_profit=float(platform_reconciliation.platform_profit),
            reconciled_at=platform_reconciliation.reconciled_at,
            statements=statement_dtos,
        )

    def mark_statement_paid(
        self, statement_id: str, request: MarkPaidRequest
    ) -> SettledStatementResponse:
        """
        Marks an individual tenant's statement as 'paid' via Bank UTR.
        """
        try:
            stmt = self.repository.mark_statement_paid(
                statement_id=statement_id,
                transaction_reference=request.transaction_reference,
                invoice_url=request.invoice_url,
            )
        except LookupError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        return SettledStatementResponse(
            statement_id=stmt.statement_id,
            tenant_id=stmt.tenant_id,
            month=stmt.month,
            amount=float(stmt.amount),
            currency=stmt.currency,
            status=stmt.status,
            transaction_reference=stmt.transaction_reference,
            settled_at=stmt.settled_at,
        )

    def get_audit_ledger(self, page: int, limit: int) -> ReconciliationListResponse:
        """
        Retrieves the paginated platform audit ledger of all reconciliations.
        """
        items, total = self.repository.get_reconciliations_ledger(
            page=page, limit=limit
        )

        dtos = []
        for item in items:
            dtos.append(
                ReconciliationListItem(
                    id=item.id,
                    month=item.month,
                    total_google_revenue=float(item.total_google_revenue),
                    platform_profit=float(item.platform_profit),
                    creator_pool_amount=float(item.creator_pool_amount),
                    currency=item.currency,
                    status=item.status,
                    reconciled_at=item.reconciled_at,
                )
            )

        return ReconciliationListResponse.create(
            items=dtos,
            total=total,
            page=page,
            limit=limit,
        )
