import hashlib
import uuid
from datetime import datetime, timezone

from peewee import fn

from app.config import get_settings
from app.database import db_proxy
from app.models.ad_monetization import (
    AdImpressionEvent,
    AdMonthlySettlement,
    AdPlatformMonthlyReconciliation,
    CreatorPayoutProfile,
)
from app.models.tenant import Tenant
from app.schemas.admin.super_admin_monetization_schemas import (
    TenantStatementDraft,
)
from app.utils.date_utils import (
    get_date_range_for_month,
    get_scheduled_payout_date,
    now_utc,
)


class SuperAdminMonetizationRepository:
    """
    Handles complex backend aggregations, ACID transactions, and mutations
    for the Super Admin Ad Revenue Reconciliation & Settlement APIs.
    """

    def generate_draft(
        self,
        month: str,
        gross_revenue: float,
        notes: str | None,
        platform_commission_pct: float,
    ) -> tuple[AdPlatformMonthlyReconciliation, list[TenantStatementDraft]]:
        """
        Calculates the draft platform reconciliation and individual tenant statements
        using live telemetry (AdImpressionEvent) data.
        Upserts the 'draft' AdPlatformMonthlyReconciliation row, but does NOT create statements in DB.
        """
        start_date, end_date = get_date_range_for_month(month)

        # 1. Query telemetry to get impression breakdown by Tenant
        tenant_stats = list(
            AdImpressionEvent.select(
                AdImpressionEvent.tenant_id,
                Tenant.name.alias("tenant_name"),
                fn.COUNT(AdImpressionEvent.id).alias("impressions_count"),
            )
            .join(Tenant, on=(AdImpressionEvent.tenant == Tenant.id))
            .where(
                AdImpressionEvent.created_at >= start_date,
                AdImpressionEvent.created_at < end_date,
                Tenant.is_active == True,
            )
            .group_by(AdImpressionEvent.tenant_id, Tenant.name)
            .dicts()
        )

        total_impressions = sum(row["impressions_count"] for row in tenant_stats)
        creators_count = len(tenant_stats)

        # 2. Perform Master Math
        platform_profit = gross_revenue * (platform_commission_pct / 100.0)
        creator_pool = gross_revenue - platform_profit

        gross_ecpm = 0.0
        creator_net_ecpm = 0.0
        if total_impressions > 0:
            gross_ecpm = (gross_revenue / total_impressions) * 1000.0
            creator_net_ecpm = (creator_pool / total_impressions) * 1000.0

        # 3. Create or update the Draft row in the Database
        with db_proxy.atomic():
            platform_draft, created = AdPlatformMonthlyReconciliation.get_or_create(
                month=month,
                defaults={
                    "total_google_revenue": gross_revenue,
                    "total_impressions": total_impressions,
                    "gross_ecpm": gross_ecpm,
                    "platform_commission_pct": platform_commission_pct,
                    "platform_profit": platform_profit,
                    "creator_pool_amount": creator_pool,
                    "creator_net_ecpm": creator_net_ecpm,
                    "creators_count": creators_count,
                    "status": "draft",
                    "notes": notes,
                },
            )

            # If it already existed but was drafted, update the numbers safely
            if not created:
                if platform_draft.status != "draft":
                    raise ValueError(
                        f"Reconciliation for month {month} has already been published."
                    )
                platform_draft.total_google_revenue = gross_revenue
                platform_draft.total_impressions = total_impressions
                platform_draft.gross_ecpm = gross_ecpm
                platform_draft.platform_commission_pct = platform_commission_pct
                platform_draft.platform_profit = platform_profit
                platform_draft.creator_pool_amount = creator_pool
                platform_draft.creator_net_ecpm = creator_net_ecpm
                platform_draft.creators_count = creators_count
                platform_draft.notes = notes
                platform_draft.save()

        # 4. Compute preview statements in memory (Do not write them to DB)
        preview_statements = []
        for row in tenant_stats:
            impressions = row["impressions_count"]
            tenant_gross = (
                (impressions / total_impressions) * gross_revenue
                if total_impressions
                else 0.0
            )
            tenant_platform_fee = tenant_gross * (platform_commission_pct / 100.0)
            net_amount = tenant_gross - tenant_platform_fee

            preview_statements.append(
                TenantStatementDraft(
                    tenant_id=row["tenant_id"],
                    tenant_name=row["tenant_name"],
                    impressions_count=impressions,
                    net_ecpm=creator_net_ecpm,
                    net_amount=net_amount,
                    gross_revenue=tenant_gross,
                    platform_fee=tenant_platform_fee,
                )
            )

        return platform_draft, preview_statements

    def publish_reconciliation(
        self, month: str
    ) -> tuple[AdPlatformMonthlyReconciliation, list[AdMonthlySettlement]]:
        """
        Locks the draft platform reconciliation and bulk inserts the official AdMonthlySettlement statements.
        Executed inside an ACID transaction to prevent partial state.
        """
        platform_draft = AdPlatformMonthlyReconciliation.get_or_none(
            AdPlatformMonthlyReconciliation.month == month
        )
        if not platform_draft:
            raise LookupError(
                f"No draft found for month {month}. Please generate a draft first."
            )

        if platform_draft.status != "draft":
            raise ValueError(
                f"Reconciliation for month {month} is already in '{platform_draft.status}' status."
            )

        start_date, end_date = get_date_range_for_month(month)

        # Re-fetch tenant impression breakdown (aligned strictly with draft active tenant rules)
        tenant_stats = list(
            AdImpressionEvent.select(
                AdImpressionEvent.tenant_id,
                fn.COUNT(AdImpressionEvent.id).alias("impressions_count"),
            )
            .join(Tenant, on=(AdImpressionEvent.tenant == Tenant.id))
            .where(
                AdImpressionEvent.created_at >= start_date,
                AdImpressionEvent.created_at < end_date,
                Tenant.is_active == True,
            )
            .group_by(AdImpressionEvent.tenant_id)
            .dicts()
        )

        total_impressions = platform_draft.total_impressions
        gross_revenue = float(platform_draft.total_google_revenue)
        platform_commission_pct = float(platform_draft.platform_commission_pct)
        creator_net_ecpm = float(platform_draft.creator_net_ecpm)

        # Identify which tenants have bank profiles for automatic 'reconciled' transition
        payout_profiles = CreatorPayoutProfile.select(CreatorPayoutProfile.tenant_id)
        tenants_with_bank = {p.tenant_id for p in payout_profiles}

        scheduled_date = None
        if total_impressions > 0:
            scheduled_date = get_scheduled_payout_date(month)

        statements_to_insert = []

        # We need the Tenant IDs mapping to Name to return nice DTOs or we can join later.
        # But for insertion we just need the data.
        with db_proxy.atomic():
            platform_draft.status = "reconciled"
            platform_draft.reconciled_at = now_utc()
            platform_draft.save()

            for row in tenant_stats:
                t_id = row["tenant_id"]
                impressions = row["impressions_count"]
                tenant_gross = (
                    (impressions / total_impressions) * gross_revenue
                    if total_impressions
                    else 0.0
                )
                tenant_platform_fee = tenant_gross * (platform_commission_pct / 100.0)
                net_amount = tenant_gross - tenant_platform_fee

                # Collision guard hash
                guard_hash = (
                    hashlib.md5(f"{month}-{t_id}-{uuid.uuid4().hex}".encode())
                    .hexdigest()[:4]
                    .upper()
                )
                stmt_id = f"STMT-{month.replace('-', '')}-TEN{t_id}-{guard_hash}"

                # State machine rules
                stmt_status = "accruing"
                if net_amount >= get_settings().MIN_PAYOUT_THRESHOLD:
                    stmt_status = (
                        "reconciled"
                        if t_id in tenants_with_bank
                        else "pending_bank_details"
                    )

                statements_to_insert.append(
                    {
                        "reconciliation_id": platform_draft.id,
                        "tenant_id": t_id,
                        "statement_id": stmt_id,
                        "month": month,
                        "impressions_count": impressions,
                        "ecpm": creator_net_ecpm,
                        "amount": net_amount,
                        "status": stmt_status,
                        "scheduled_payout_date": scheduled_date,
                        "gross_revenue": tenant_gross,
                        "platform_commission_pct": platform_commission_pct,
                        "platform_fee": tenant_platform_fee,
                    }
                )

            if statements_to_insert:
                # Bulk insert in batches of 100 to avoid query limits on large platforms
                for batch in range(0, len(statements_to_insert), 100):
                    AdMonthlySettlement.insert_many(
                        statements_to_insert[batch : batch + 100]
                    ).execute()

        # Fetch the newly created statements with Tenant names attached for the response
        new_statements = list(
            AdMonthlySettlement.select(AdMonthlySettlement, Tenant)
            .join(Tenant, on=(AdMonthlySettlement.tenant == Tenant.id))
            .where(AdMonthlySettlement.reconciliation == platform_draft)
            .order_by(AdMonthlySettlement.amount.desc())
        )
        return platform_draft, new_statements

    def mark_statement_paid(
        self, statement_id: str, transaction_reference: str, invoice_url: str | None
    ) -> AdMonthlySettlement:
        """Updates a statement's status to 'paid' and records the UTR reference."""
        stmt = AdMonthlySettlement.get_or_none(
            AdMonthlySettlement.statement_id == statement_id
        )
        if not stmt:
            raise LookupError("Statement not found")
        if stmt.status == "paid":
            raise ValueError("Statement is already paid")
        if stmt.status != "reconciled":
            raise ValueError(
                f"Cannot pay statement in '{stmt.status}' status. Must be 'reconciled'."
            )

        with db_proxy.atomic():
            stmt.status = "paid"
            stmt.transaction_reference = transaction_reference
            stmt.invoice_url = invoice_url
            stmt.settled_at = datetime.now(timezone.utc)
            stmt.save()

        return stmt

    def get_reconciliations_ledger(
        self, page: int, limit: int
    ) -> tuple[list[AdPlatformMonthlyReconciliation], int]:
        """Returns paginated platform reconciliations."""
        query = AdPlatformMonthlyReconciliation.select().order_by(
            AdPlatformMonthlyReconciliation.month.desc()
        )
        total = query.count()
        items = list(query.paginate(page, limit))
        return items, total
