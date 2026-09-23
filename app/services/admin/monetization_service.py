import math
import re
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status

from app.config import get_settings
from app.models.video import Video
from app.repositories.admin.monetization_repository import MonetizationRepository
from app.schemas.admin.monetization_schemas import (
    CurrentPeriodSummary,
    LastPayoutSummary,
    MonetizationAnalyticsPoint,
    MonetizationAnalyticsResponse,
    MonetizationSummaryResponse,
    PayoutProfileResponse,
    PayoutProfileUpdateRequest,
    PendingPayoutSummary,
    SettlementItemResponse,
    SettlementsListResponse,
)
from app.utils.auth import is_tenant_active
from app.utils.date_utils import get_app_timezone

# Recognized Indian Bank IFSC 4-character prefix lookup dictionary
IFSC_BANK_PREFIX_MAP: dict[str, str] = {
    "HDFC": "HDFC Bank",
    "SBIN": "State Bank of India",
    "ICIC": "ICICI Bank",
    "UTIB": "Axis Bank",
    "KKBK": "Kotak Mahindra Bank",
    "PUNB": "Punjab National Bank",
    "BARB": "Bank of Baroda",
    "CNRB": "Canara Bank",
    "UBIN": "Union Bank of India",
    "IDFB": "IDFC First Bank",
    "YESB": "Yes Bank",
    "INDB": "IndusInd Bank",
    "IOBA": "Indian Overseas Bank",
    "BKID": "Bank of India",
    "MAHB": "Bank of Maharashtra",
    "CBIN": "Central Bank of India",
    "FDRL": "Federal Bank",
    "CIUB": "City Union Bank",
    "KVBL": "Karur Vysya Bank",
    "RBLN": "RBL Bank",
    "AUBL": "AU Small Finance Bank",
    "ESFB": "Equitas Small Finance Bank",
    "AIRP": "Airtel Payments Bank",
    "PYTM": "Paytm Payments Bank",
    "IPOS": "India Post Payments Bank",
}


def resolve_bank_name_from_ifsc(ifsc: str) -> str:
    """Auto-resolves the official bank institution name from the 11-char IFSC code."""
    if not ifsc or len(ifsc) < 4:
        return "Bank"
    prefix = ifsc[:4].upper()
    return IFSC_BANK_PREFIX_MAP.get(prefix, f"{prefix} Bank")


def mask_account_number(account_no: str | None) -> str | None:
    """Masks bank account number, displaying only the terminal 4 digits (e.g. ••••••••4589)."""
    if not account_no:
        return None
    clean = account_no.strip()
    if len(clean) <= 4:
        return "••••" + clean
    return "••••••••" + clean[-4:]


class MonetizationService:
    """
    Business logic layer for Creator Ad Monetization,
    Telemetry Ingestion, and Monthly Settlement Reconciliation.
    """

    def __init__(self, repo: MonetizationRepository | None = None) -> None:
        self.repo = repo or MonetizationRepository()

    def get_monetization_summary(self, tenant_id: int) -> MonetizationSummaryResponse:
        """
        Computes active month impressions, dynamic historical eCPM,
        expected payout schedule, and pending/last payout status.
        """
        settings = get_settings()
        tz = get_app_timezone()
        now_local = datetime.now(tz)
        current_month_str = now_local.strftime("%Y-%m")

        # 1. Active month UTC date boundaries
        first_day_local = now_local.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # Next calendar month
        if first_day_local.month == 12:
            next_month_local = first_day_local.replace(year=first_day_local.year + 1, month=1)
        else:
            next_month_local = first_day_local.replace(month=first_day_local.month + 1)

        first_day_utc = first_day_local.astimezone(timezone.utc)
        now_utc = datetime.now(timezone.utc)

        # 2. Count active month impressions (100% factual ground truth counter)
        impressions_count = self.repo.count_impressions_in_window(
            tenant_id=tenant_id, start_dt=first_day_utc, end_dt=now_utc
        )

        # 3. Dynamic eCPM Resolution:
        # Check if creator has at least 1 settled past payout. If so, use historical baseline.
        # If new creator, return null (accruing) to avoid any misleading default promises.
        historical_ecpm = self.repo.get_latest_settled_ecpm(tenant_id)
        if historical_ecpm is not None and historical_ecpm > 0:
            ecpm: float | None = round(historical_ecpm, 2)
            estimated_earnings: float | None = round(
                (impressions_count * ecpm) / 1000.0, 2
            )
        else:
            ecpm = None
            estimated_earnings = None

        expected_payout_date = (
            f"{next_month_local.strftime('%Y-%m')}-{settings.PAYOUT_DAY_OF_MONTH:02d}"
        )

        current_period = CurrentPeriodSummary(
            period=current_month_str,
            estimated_earnings=estimated_earnings,
            impressions=impressions_count,
            ecpm=ecpm,
            expected_payout_date=expected_payout_date,
        )

        # 4. Payout Profile Check
        profile = self.repo.get_payout_profile(tenant_id)
        payout_profile_configured = bool(
            profile
            and profile.account_number
            and profile.ifsc_code
            and profile.account_holder_name
        )

        # 5. Pending Payout Resolution
        pending_stmt = self.repo.get_pending_settlement(tenant_id)
        pending_payout: PendingPayoutSummary | None = None
        if pending_stmt:
            # If bank details are missing, hold state as pending_bank_details
            current_status = pending_stmt.status
            if not payout_profile_configured and current_status == "reconciled":
                current_status = "pending_bank_details"

            payout_date_str = (
                str(pending_stmt.scheduled_payout_date)
                if pending_stmt.scheduled_payout_date
                else expected_payout_date
            )
            pending_payout = PendingPayoutSummary(
                period=pending_stmt.month,
                amount=float(pending_stmt.amount),
                status=current_status,
                payout_date=payout_date_str,
            )

        # 6. Last Payout Resolution
        last_stmt = self.repo.get_last_paid_settlement(tenant_id)
        last_payout: LastPayoutSummary | None = None
        if last_stmt:
            settled_at_str = (
                last_stmt.settled_at.strftime("%Y-%m-%d")
                if last_stmt.settled_at
                else str(last_stmt.scheduled_payout_date or "")
            )
            last_payout = LastPayoutSummary(
                period=last_stmt.month,
                amount=float(last_stmt.amount),
                payout_date=settled_at_str,
                utr=last_stmt.transaction_reference,
            )

        # 7. Lifetime Earnings
        lifetime_earnings = self.repo.get_lifetime_settled_earnings(tenant_id)

        return MonetizationSummaryResponse(
            currency=settings.DEFAULT_CURRENCY,
            payout_profile_configured=payout_profile_configured,
            current_period=current_period,
            pending_payout=pending_payout,
            last_payout=last_payout,
            lifetime_earnings=lifetime_earnings,
        )

    def get_monetization_analytics(
        self,
        tenant_id: int,
        range_preset: str | None = "30d",
        start_date_str: str | None = None,
        end_date_str: str | None = None,
        interval: str | None = None,
    ) -> MonetizationAnalyticsResponse:
        """
        Generates granular time-series impressions and estimated earnings data
        for rendering interactive charts in the Creator Studio portal.
        """
        settings = get_settings()
        now_local = datetime.now(get_app_timezone())
        today = now_local.date()

        # Resolve date boundaries
        if start_date_str and end_date_str:
            try:
                start_d = date.fromisoformat(start_date_str)
                end_d = date.fromisoformat(end_date_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ISO date format. Expected YYYY-MM-DD.",
                )
            if start_d > end_d:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_date cannot be after end_date.",
                )
        else:
            preset = (range_preset or "30d").lower().strip()
            preset_map = {
                "7d": 7,
                "30d": 30,
                "90d": 90,
                "6m": 180,
                "12m": 365,
            }
            days = preset_map.get(preset, 30)
            end_d = today
            start_d = end_d - timedelta(days=days - 1)

        # Auto-resolve grouping interval if omitted
        duration_days = (end_d - start_d).days + 1
        if not interval:
            if duration_days <= 30:
                resolved_interval = "day"
            elif duration_days <= 90:
                resolved_interval = "week"
            else:
                resolved_interval = "month"
        else:
            resolved_interval = interval.lower().strip()
            if resolved_interval not in {"day", "week", "month"}:
                resolved_interval = "day"

        # Query UTC date window converted from local app timezone
        tz = get_app_timezone()
        start_dt_local = datetime(
            start_d.year, start_d.month, start_d.day, 0, 0, 0, tzinfo=tz
        )
        end_dt_local = datetime(
            end_d.year, end_d.month, end_d.day, 23, 59, 59, 999999, tzinfo=tz
        )
        start_dt_utc = start_dt_local.astimezone(timezone.utc)
        end_dt_utc = end_dt_local.astimezone(timezone.utc)

        daily_counts = self.repo.get_daily_impressions(
            tenant_id=tenant_id, start_dt=start_dt_utc, end_dt=end_dt_utc
        )

        # Dynamic eCPM baseline
        baseline_ecpm = self.repo.get_latest_settled_ecpm(tenant_id)

        # Bucket points chronologically
        data_points: list[MonetizationAnalyticsPoint] = []

        if resolved_interval == "day":
            curr = start_d
            while curr <= end_d:
                d_str = curr.isoformat()
                imp = daily_counts.get(d_str, 0)
                if baseline_ecpm is not None and baseline_ecpm > 0:
                    pt_ecpm: float | None = round(baseline_ecpm, 2)
                    pt_earnings: float | None = round((imp * pt_ecpm) / 1000.0, 2)
                else:
                    pt_ecpm = None
                    pt_earnings = None

                data_points.append(
                    MonetizationAnalyticsPoint(
                        date=d_str,
                        impressions=imp,
                        ecpm=pt_ecpm,
                        estimated_earnings=pt_earnings,
                    )
                )
                curr += timedelta(days=1)

        elif resolved_interval == "week":
            curr = start_d
            while curr <= end_d:
                week_end = min(curr + timedelta(days=6), end_d)
                week_imp = 0
                step = curr
                while step <= week_end:
                    week_imp += daily_counts.get(step.isoformat(), 0)
                    step += timedelta(days=1)

                if baseline_ecpm is not None and baseline_ecpm > 0:
                    pt_ecpm = round(baseline_ecpm, 2)
                    pt_earnings = round((week_imp * pt_ecpm) / 1000.0, 2)
                else:
                    pt_ecpm = None
                    pt_earnings = None

                data_points.append(
                    MonetizationAnalyticsPoint(
                        date=curr.isoformat(),
                        impressions=week_imp,
                        ecpm=pt_ecpm,
                        estimated_earnings=pt_earnings,
                    )
                )
                curr = week_end + timedelta(days=1)

        else:  # month
            curr = start_d
            while curr <= end_d:
                # Find end of month
                if curr.month == 12:
                    month_end = date(curr.year, 12, 31)
                else:
                    month_end = date(curr.year, curr.month + 1, 1) - timedelta(days=1)
                bucket_end = min(month_end, end_d)

                month_imp = 0
                step = curr
                while step <= bucket_end:
                    month_imp += daily_counts.get(step.isoformat(), 0)
                    step += timedelta(days=1)

                if baseline_ecpm is not None and baseline_ecpm > 0:
                    pt_ecpm = round(baseline_ecpm, 2)
                    pt_earnings = round((month_imp * pt_ecpm) / 1000.0, 2)
                else:
                    pt_ecpm = None
                    pt_earnings = None

                data_points.append(
                    MonetizationAnalyticsPoint(
                        date=curr.isoformat(),
                        impressions=month_imp,
                        ecpm=pt_ecpm,
                        estimated_earnings=pt_earnings,
                    )
                )
                curr = bucket_end + timedelta(days=1)

        return MonetizationAnalyticsResponse(
            start_date=start_d.isoformat(),
            end_date=end_d.isoformat(),
            interval=resolved_interval,
            currency=settings.DEFAULT_CURRENCY,
            data_points=data_points,
        )

    def get_settlement_history(
        self, tenant_id: int, page: int = 1, limit: int = 12
    ) -> SettlementsListResponse:
        """Returns paginated itemized monthly settlement statements."""
        settings = get_settings()
        records, total = self.repo.get_settlements_paginated(
            tenant_id=tenant_id, page=page, limit=limit
        )
        total_pages = math.ceil(total / limit) if total > 0 else 1

        items: list[SettlementItemResponse] = []
        for r in records:
            items.append(
                SettlementItemResponse(
                    statement_id=r.statement_id,
                    month=r.month,
                    impressions_count=int(r.impressions_count),
                    ecpm=round(float(r.ecpm), 2),
                    amount=round(float(r.amount), 2),
                    currency=r.currency or settings.DEFAULT_CURRENCY,
                    status=r.status,
                    settled_at=r.settled_at,
                    transaction_reference=r.transaction_reference,
                    invoice_url=r.invoice_url,
                )
            )

        return SettlementsListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
        )

    def get_payout_profile(self, tenant_id: int) -> PayoutProfileResponse:
        """Retrieves creator bank payout profile with masked account number."""
        profile = self.repo.get_payout_profile(tenant_id)
        if not profile:
            return PayoutProfileResponse()

        return PayoutProfileResponse(
            account_holder_name=profile.account_holder_name,
            bank_name=profile.bank_name,
            account_number_masked=mask_account_number(profile.account_number),
            ifsc_code=profile.ifsc_code,
            updated_at=profile.updated_at,
        )

    def update_payout_profile(
        self, tenant_id: int, request: PayoutProfileUpdateRequest
    ) -> PayoutProfileResponse:
        """
        Registers or updates creator bank payout details.
        Auto-resolves bank name from IFSC code on write.
        If any statement was held in 'pending_bank_details', releases it to 'reconciled'.
        """
        clean_ifsc = request.ifsc_code.strip().upper()
        if not re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", clean_ifsc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid IFSC code format. Expected 11 alphanumeric characters (e.g. HDFC0000128).",
            )

        clean_account = request.account_number.strip()
        if not clean_account.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account number must contain numeric digits only.",
            )

        bank_name = resolve_bank_name_from_ifsc(clean_ifsc)
        holder_name = request.account_holder_name.strip()

        profile = self.repo.upsert_payout_profile(
            tenant_id=tenant_id,
            account_holder_name=holder_name,
            account_number=clean_account,
            ifsc_code=clean_ifsc,
            bank_name=bank_name,
        )

        # Release all pending statements held for missing bank details
        self.repo.release_all_pending_bank_statements(tenant_id)

        return PayoutProfileResponse(
            account_holder_name=profile.account_holder_name,
            bank_name=profile.bank_name,
            account_number_masked=mask_account_number(profile.account_number),
            ifsc_code=profile.ifsc_code,
            updated_at=profile.updated_at,
        )

    def record_ad_impression(
        self,
        video_id: int,
        subscriber_id: int,
        event_type: str = "impression",
        ad_duration_seconds: int = 0,
    ) -> None:
        """
        Processes and logs a verified video ad impression beacon from mobile clients.
        Enforces:
          1. Valid video asset existence (raises 404 if missing).
          2. Active creator attribution (gracefully discards if unassigned).
          3. Event type filtering: only primary 'impression' milestones increment billable counts.
          4. Rapid-fire debounce from settings (supports podded ads, stops script spam).
          5. Session frequency cap from settings (prevents infinite loop/bot spam).
        """
        settings = get_settings()

        video = Video.get_or_none(Video.id == video_id)
        if not video:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Video asset with ID {video_id} not found.",
            )

        tenant_id = video.tenant_id
        if not is_tenant_active(tenant_id):
            # Video does not have an active creator owner; ignore quietly
            return

        # Only primary "impression" event triggers the billable ad impression count
        if event_type != "impression":
            # Milestone events (midpoint, complete) acknowledged with 204 No Content
            return

        now_utc = datetime.now(timezone.utc)

        # 1. Rapid-fire debounce between consecutive ad beacons on the same video
        last_imp = self.repo.get_last_ad_impression(subscriber_id, video_id)
        if last_imp and last_imp.created_at:
            delta = (
                now_utc - last_imp.created_at.replace(tzinfo=timezone.utc)
            ).total_seconds()
            if delta < settings.AD_IMPRESSION_DEBOUNCE_SECONDS:
                # Debounced: silently accept without double counting
                return

        # 2. Session frequency cap per user per video
        window_session = now_utc - timedelta(
            minutes=settings.AD_IMPRESSION_SESSION_WINDOW_MINUTES
        )
        recent_count = self.repo.count_recent_impressions(
            subscriber_id=subscriber_id,
            video_id=video_id,
            since_dt=window_session,
        )
        if recent_count >= settings.AD_IMPRESSION_MAX_PER_SESSION:
            # Frequency capped
            return

        # Append verified impression to the ledger
        self.repo.log_ad_impression(
            tenant_id=tenant_id, video_id=video_id, subscriber_id=subscriber_id
        )
