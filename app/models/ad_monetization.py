from peewee import (
    BigIntegerField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from app.config import get_settings
from app.models.base import BaseModel
from app.models.subscriber import Subscriber
from app.models.tenant import Tenant
from app.models.video import Video
from app.utils.date_utils import now_utc


class AdImpressionEvent(BaseModel):
    """
    Immutable event ledger for every validated video ad impression beacon rendered on mobile.
    Enforces high-throughput telemetry counting and fraud prevention debouncing.
    """

    tenant = ForeignKeyField(
        model=Tenant,
        column_name="tenant_id",
        backref="ad_impressions",
        on_delete="CASCADE",
        index=True,
    )
    video = ForeignKeyField(
        model=Video,
        column_name="video_id",
        backref="ad_impressions",
        on_delete="CASCADE",
    )
    subscriber = ForeignKeyField(
        model=Subscriber,
        column_name="subscriber_id",
        backref="ad_impressions",
        on_delete="CASCADE",
    )
    created_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "ad_impression_events"
        indexes = (
            (("tenant", "created_at"), False),
            (("video", "created_at"), False),
            (("video", "subscriber", "created_at"), False),
        )


class AdPlatformMonthlyReconciliation(BaseModel):
    """
    Master Platform Revenue & Commission Ledger.
    Stores company-wide monthly gross ad revenue from Google Ad Manager,
    platform 30% retained technology profit, and creator pool disbursement totals.
    """

    month = CharField(max_length=7, unique=True, index=True)  # Format: "YYYY-MM"
    total_google_revenue = DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_impressions = BigIntegerField(default=0)
    gross_ecpm = DecimalField(max_digits=10, decimal_places=4, default=0.0)
    platform_commission_pct = DecimalField(
        max_digits=5,
        decimal_places=2,
        default=lambda: get_settings().PLATFORM_AD_COMMISSION_PERCENT,
    )
    platform_profit = DecimalField(max_digits=12, decimal_places=2, default=0.0)
    creator_pool_amount = DecimalField(max_digits=12, decimal_places=2, default=0.0)
    creator_net_ecpm = DecimalField(max_digits=10, decimal_places=4, default=0.0)
    creators_count = IntegerField(default=0)
    currency = CharField(max_length=10, default=lambda: get_settings().DEFAULT_CURRENCY)
    status = CharField(
        max_length=20, default="reconciled", index=True
    )  # draft, reconciled, disbursed
    reconciled_at = DateTimeField(null=True)
    notes = TextField(null=True)

    class Meta:
        table_name = "ad_platform_monthly_reconciliations"


class AdMonthlySettlement(BaseModel):
    """
    Itemized monthly payout statement and UTR bank settlement ledger for each tenant creator.
    Linked to the platform monthly reconciliation run via reconciliation_id.
    """

    reconciliation = ForeignKeyField(
        model=AdPlatformMonthlyReconciliation,
        column_name="reconciliation_id",
        backref="settlements",
        null=True,
        on_delete="CASCADE",
    )
    tenant = ForeignKeyField(
        model=Tenant,
        column_name="tenant_id",
        backref="ad_settlements",
        on_delete="CASCADE",
        index=True,
    )
    statement_id = CharField(
        max_length=50, unique=True, index=True
    )  # e.g. "STMT-202609-TEN42-8F9B"
    month = CharField(max_length=7, index=True)  # Format: "YYYY-MM"
    impressions_count = BigIntegerField(default=0)
    ecpm = DecimalField(max_digits=10, decimal_places=4, default=0.0)
    amount = DecimalField(max_digits=12, decimal_places=2, default=0.0)
    currency = CharField(max_length=10, default=lambda: get_settings().DEFAULT_CURRENCY)
    status = CharField(
        max_length=30, default="accruing", index=True
    )  # accruing, pending_bank_details, reconciled, paid
    scheduled_payout_date = DateField(null=True)
    settled_at = DateTimeField(null=True)
    transaction_reference = CharField(max_length=100, null=True)  # Bank UTR
    invoice_url = CharField(max_length=500, null=True)

    # Internal platform audit columns (strictly hidden from creator-facing APIs)
    gross_revenue = DecimalField(max_digits=12, decimal_places=2, default=0.0)
    platform_commission_pct = DecimalField(
        max_digits=5,
        decimal_places=2,
        default=lambda: get_settings().PLATFORM_AD_COMMISSION_PERCENT,
    )
    platform_fee = DecimalField(max_digits=12, decimal_places=2, default=0.0)

    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "ad_monthly_settlements"
        indexes = (
            (("tenant", "month"), True),  # Exactly one settlement per tenant per month
            (("tenant", "status"), False),
            (("reconciliation",), False),
        )


class CreatorPayoutProfile(BaseModel):
    """
    Bank payout profile for automated tenant creator revenue disbursements.
    Bank name is auto-resolved from the IFSC code on write.
    """

    tenant = ForeignKeyField(
        model=Tenant,
        column_name="tenant_id",
        backref="payout_profile",
        unique=True,
        on_delete="CASCADE",
        index=True,
    )
    account_holder_name = CharField(max_length=100, null=True)
    account_number = CharField(max_length=50, null=True)
    ifsc_code = CharField(max_length=20, null=True)
    bank_name = CharField(max_length=100, null=True)
    created_at = DateTimeField(default=now_utc)
    updated_at = DateTimeField(default=now_utc)

    class Meta:
        table_name = "creator_payout_profiles"
