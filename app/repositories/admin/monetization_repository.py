from datetime import datetime, timezone

from peewee import fn

from app.models.ad_monetization import (
    AdImpressionEvent,
    AdMonthlySettlement,
    CreatorPayoutProfile,
)


class MonetizationRepository:
    """
    Encapsulates database queries and aggregations for the Ad Monetization,
    Telemetry Ingestion, and Monthly Revenue Settlement subsystem.
    """

    def log_ad_impression(
        self, creator_id: int, video_id: int, subscriber_id: int
    ) -> AdImpressionEvent:
        """Appends an immutable video ad impression beacon record."""
        return AdImpressionEvent.create(
            creator_id=creator_id,
            video_id=video_id,
            subscriber_id=subscriber_id,
            created_at=datetime.now(timezone.utc),
        )

    def get_last_ad_impression(
        self, subscriber_id: int, video_id: int
    ) -> AdImpressionEvent | None:
        """
        Retrieves the most recent ad impression beacon for this subscriber and video.
        Used for rapid-fire anti-spam debounce check.
        """
        return (
            AdImpressionEvent.select()
            .where(
                AdImpressionEvent.subscriber == subscriber_id,
                AdImpressionEvent.video == video_id,
            )
            .order_by(AdImpressionEvent.created_at.desc())
            .first()
        )

    def count_recent_impressions(
        self, subscriber_id: int, video_id: int, since_dt: datetime
    ) -> int:
        """
        Counts ad impressions for a subscriber on a video since a specific timestamp.
        Used to enforce maximum session frequency caps.
        """
        count = (
            AdImpressionEvent.select(fn.COUNT(AdImpressionEvent.id))
            .where(
                AdImpressionEvent.subscriber == subscriber_id,
                AdImpressionEvent.video == video_id,
                AdImpressionEvent.created_at >= since_dt,
            )
            .scalar()
        )
        return int(count or 0)

    def count_impressions_in_window(
        self, creator_id: int, start_dt: datetime, end_dt: datetime
    ) -> int:
        """
        Counts verified billable ad impressions for a creator within a date window.
        Utilizes composite index (creator_id, created_at).
        """
        count = (
            AdImpressionEvent.select(fn.COUNT(AdImpressionEvent.id))
            .where(
                AdImpressionEvent.creator == creator_id,
                AdImpressionEvent.created_at >= start_dt,
                AdImpressionEvent.created_at <= end_dt,
            )
            .scalar()
        )
        return int(count or 0)

    def get_daily_impressions(
        self, creator_id: int, start_dt: datetime, end_dt: datetime
    ) -> dict[str, int]:
        """
        Aggregates impressions bucketed by UTC date string 'YYYY-MM-DD'.
        """
        date_col = fn.DATE(AdImpressionEvent.created_at)
        query = (
            AdImpressionEvent.select(
                date_col.alias("d"), fn.COUNT(AdImpressionEvent.id).alias("cnt")
            )
            .where(
                AdImpressionEvent.creator == creator_id,
                AdImpressionEvent.created_at >= start_dt,
                AdImpressionEvent.created_at <= end_dt,
            )
            .group_by(date_col)
        )
        return {str(row.d): int(row.cnt) for row in query}

    def get_latest_settled_ecpm(self, creator_id: int) -> float | None:
        """
        Retrieves the most recent settled net eCPM rate for this creator.
        Returns None for brand-new creators with zero settled payout history.
        """
        settlement = (
            AdMonthlySettlement.select(AdMonthlySettlement.ecpm)
            .where(
                AdMonthlySettlement.creator == creator_id,
                AdMonthlySettlement.status == "paid",
            )
            .order_by(AdMonthlySettlement.month.desc())
            .first()
        )
        if settlement and settlement.ecpm:
            return float(settlement.ecpm)
        return None

    def get_pending_settlement(self, creator_id: int) -> AdMonthlySettlement | None:
        """
        Fetches the latest closed month settlement awaiting disbursement
        (status 'reconciled' or 'pending_bank_details').
        """
        return (
            AdMonthlySettlement.select()
            .where(
                AdMonthlySettlement.creator == creator_id,
                AdMonthlySettlement.status.in_(["reconciled", "pending_bank_details"]),
            )
            .order_by(AdMonthlySettlement.month.desc())
            .first()
        )

    def release_all_pending_bank_statements(self, creator_id: int) -> int:
        """
        Releases ALL statements held in 'pending_bank_details' to 'reconciled'
        when the creator saves their bank payout profile.
        Returns the number of statements updated.
        """
        now_utc = datetime.now(timezone.utc)
        return (
            AdMonthlySettlement.update(status="reconciled", updated_at=now_utc)
            .where(
                (AdMonthlySettlement.creator == creator_id)
                & (AdMonthlySettlement.status == "pending_bank_details")
            )
            .execute()
        )

    def get_last_paid_settlement(self, creator_id: int) -> AdMonthlySettlement | None:
        """Fetches the latest completed disbursement record with UTR reference."""
        return (
            AdMonthlySettlement.select()
            .where(
                AdMonthlySettlement.creator == creator_id,
                AdMonthlySettlement.status == "paid",
            )
            .order_by(AdMonthlySettlement.month.desc())
            .first()
        )

    def get_lifetime_settled_earnings(self, creator_id: int) -> float:
        """Sums all net payouts disbursed to creator's bank account across all time."""
        total = (
            AdMonthlySettlement.select(
                fn.COALESCE(fn.SUM(AdMonthlySettlement.amount), 0.0)
            )
            .where(
                AdMonthlySettlement.creator == creator_id,
                AdMonthlySettlement.status == "paid",
            )
            .scalar()
        )
        return round(float(total or 0.0), 2)

    def get_settlements_paginated(
        self, creator_id: int, page: int = 1, limit: int = 12
    ) -> tuple[list[AdMonthlySettlement], int]:
        """
        Fetches paginated settlement statements ordered by billing month descending.
        """
        query = (
            AdMonthlySettlement.select()
            .where(AdMonthlySettlement.creator == creator_id)
            .order_by(AdMonthlySettlement.month.desc())
        )
        total = query.count()
        items = list(query.paginate(page, limit))
        return items, total

    def get_payout_profile(self, creator_id: int) -> CreatorPayoutProfile | None:
        """Fetches the 1:1 CreatorPayoutProfile record."""
        return (
            CreatorPayoutProfile.select()
            .where(CreatorPayoutProfile.creator == creator_id)
            .first()
        )

    def upsert_payout_profile(
        self,
        creator_id: int,
        account_holder_name: str,
        account_number: str,
        ifsc_code: str,
        bank_name: str,
    ) -> CreatorPayoutProfile:
        """Atomically registers or updates creator bank payout details."""
        now = datetime.now(timezone.utc)
        profile, _ = CreatorPayoutProfile.get_or_create(
            creator_id=creator_id,
            defaults={
                "account_holder_name": account_holder_name,
                "account_number": account_number,
                "ifsc_code": ifsc_code,
                "bank_name": bank_name,
                "created_at": now,
                "updated_at": now,
            },
        )
        profile.account_holder_name = account_holder_name
        profile.account_number = account_number
        profile.ifsc_code = ifsc_code
        profile.bank_name = bank_name
        profile.updated_at = now
        profile.save()
        return profile
