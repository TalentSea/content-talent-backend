import argparse
import re
import sys
import uuid
from datetime import date, datetime, timezone

from peewee import fn

from app.config import get_settings
from app.database import db_proxy, init_db
from app.models.ad_monetization import (
    AdImpressionEvent,
    AdMonthlySettlement,
    AdPlatformMonthlyReconciliation,
    CreatorPayoutProfile,
)
from app.models.admin import Admin
from app.utils.date_utils import get_app_timezone

MONTH_REGEX = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def display_history() -> None:
    """Prints the historical master ledger of all past monthly platform reconciliations."""
    records = list(
        AdPlatformMonthlyReconciliation.select().order_by(
            AdPlatformMonthlyReconciliation.month.desc()
        )
    )
    if not records:
        print("\nNo monthly reconciliations found in the platform ledger.\n")
        return

    print("\n" + "=" * 94)
    print("                      TALENTSEA PLATFORM REVENUE & PROFIT HISTORY")
    print("=" * 94)
    header = f"{'Month':<9} {'Total Views':<13} {'Google Revenue':<16} {'Platform Profit (30%)':<24} {'Creator Pool':<16} {'Creators':<9} {'Status':<10}"
    print(header)
    print("-" * 94)

    total_views = 0
    total_revenue = 0.0
    total_profit = 0.0
    total_pool = 0.0

    for r in records:
        v = int(r.total_impressions)
        rev = float(r.total_google_revenue)
        prof = float(r.platform_profit)
        pool = float(r.creator_pool_amount)

        total_views += v
        total_revenue += rev
        total_profit += prof
        total_pool += pool

        print(
            f"{r.month:<9} {v:<13,d} ₹{rev:<14,.2f} ₹{prof:<22,.2f} ₹{pool:<14,.2f} {r.creators_count:<9} {r.status:<10}"
        )

    print("-" * 94)
    print(
        f"{'TOTALS':<9} {total_views:<13,d} ₹{total_revenue:<14,.2f} ₹{total_profit:<22,.2f} ₹{total_pool:<14,.2f}"
    )
    print("=" * 94 + "\n")


def mark_statement_paid(statement_id: str, utr: str) -> None:
    """Updates an itemized settlement record to 'paid' and records the bank UTR."""
    stmt = (
        AdMonthlySettlement.select()
        .where(AdMonthlySettlement.statement_id == statement_id.strip())
        .first()
    )
    if not stmt:
        print(f"\n❌ Error: Settlement statement '{statement_id}' not found.\n")
        sys.exit(1)

    now_utc = datetime.now(timezone.utc)
    stmt.status = "paid"
    stmt.transaction_reference = utr.strip()
    stmt.settled_at = now_utc
    stmt.updated_at = now_utc
    stmt.save()

    print("\n" + "=" * 60)
    print("✔ STATEMENT DISBURSEMENT CONFIRMED")
    print("=" * 60)
    print(f"  Statement ID:    {stmt.statement_id}")
    print(f"  Billing Month:   {stmt.month}")
    print(f"  Creator ID:      {stmt.creator_id}")
    print(f"  Amount:          ₹{float(stmt.amount):,.2f}")
    print(f"  Bank UTR:        {stmt.transaction_reference}")
    print(f"  Settled At:      {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("  Status:          PAID")
    print("=" * 60 + "\n")


def reconcile_month(
    month: str,
    revenue: float | None = None,
    ecpm: float | None = None,
    auto_confirm: bool = False,
) -> None:
    """
    Executes the monthly ad revenue settlement reconciliation:
    1. Aggregates verified impressions for the calendar month in IST.
    2. Calculates gross revenue, platform 30% cut, and creator 70% pool.
    3. Handles minimum payout threshold rollover and bank profile checks.
    4. Records the Master Platform Reconciliation and individual Creator Statements.
    """
    settings = get_settings()

    if not MONTH_REGEX.match(month):
        print(
            f"\n❌ Error: Invalid month format '{month}'. Expected 'YYYY-MM' (e.g. 2026-09).\n"
        )
        sys.exit(1)

    if revenue is None and ecpm is None:
        print("\n❌ Error: Must specify either --revenue <FLOAT> or --ecpm <FLOAT>.\n")
        sys.exit(1)

    # 1. Resolve local platform operating month date boundaries
    tz = get_app_timezone()
    year, m = map(int, month.split("-"))
    start_dt_local = datetime(year, m, 1, 0, 0, 0, tzinfo=tz)
    if m == 12:
        end_dt_local = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=tz)
    else:
        end_dt_local = datetime(year, m + 1, 1, 0, 0, 0, tzinfo=tz)

    start_dt_utc = start_dt_local.astimezone(timezone.utc)
    end_dt_utc = end_dt_local.astimezone(timezone.utc)

    # 2. Query impressions per creator for this month
    query = (
        AdImpressionEvent.select(
            AdImpressionEvent.creator.alias("creator_id"),
            fn.COUNT(AdImpressionEvent.id).alias("cnt"),
        )
        .where(
            AdImpressionEvent.created_at >= start_dt_utc,
            AdImpressionEvent.created_at < end_dt_utc,
        )
        .group_by(AdImpressionEvent.creator)
    )

    creator_counts: dict[int, int] = {
        int(row.creator_id): int(row.cnt) for row in query
    }
    total_impressions = sum(creator_counts.values())

    if total_impressions == 0:
        print(
            f"\n⚠️ Warning: No verified ad impressions found for billing month '{month}'."
        )
        print("  Statements cannot be generated for an empty month.\n")
        sys.exit(0)

    # 3. Calculate financial figures
    if revenue is not None:
        gross_revenue = float(revenue)
        gross_ecpm = (gross_revenue / total_impressions) * 1000.0
    else:
        gross_ecpm = float(ecpm)
        gross_revenue = (total_impressions * gross_ecpm) / 1000.0

    commission_pct = settings.PLATFORM_AD_COMMISSION_PERCENT  # e.g. 30.0%
    platform_profit = gross_revenue * (commission_pct / 100.0)
    creator_pool = gross_revenue - platform_profit
    creator_net_ecpm = gross_ecpm * (1.0 - (commission_pct / 100.0))
    min_threshold = settings.MIN_PAYOUT_THRESHOLD  # e.g. 500.0

    # Scheduled payout date (28th of following month)
    payout_month = m + 1 if m < 12 else 1
    payout_year = year if m < 12 else year + 1
    scheduled_payout_date = date(
        payout_year, payout_month, settings.PAYOUT_DAY_OF_MONTH
    )

    # 4. Preview in Terminal
    print("\n" + "=" * 66)
    print("          TALENTSEA AD REVENUE MONTHLY RECONCILIATION")
    print("=" * 66)
    print(f"  Billing Month:          {month}")
    print(f"  Total Verified Views:   {total_impressions:,d}")
    print(f"  Google Gross Revenue:   ₹{gross_revenue:,.2f}")
    print(f"  Calculated Gross eCPM:  ₹{gross_ecpm:,.2f} per 1,000 views")
    print(
        f"  Platform Cut ({commission_pct:g}%):     ₹{platform_profit:,.2f}  (Platform Retained Profit)"
    )
    print(
        f"  Creator Net Pool ({100 - commission_pct:g}%): ₹{creator_pool:,.2f}  (Creator Net eCPM: ₹{creator_net_ecpm:,.2f})"
    )
    print(f"  Scheduled Payout Date:  {scheduled_payout_date.isoformat()}")
    print("-" * 66)
    print("CREATOR BREAKDOWN:")
    print(
        f"  {'Creator ID':<12} {'Studio / Name':<20} {'Impressions':<13} {'Net Payout':<13} {'Status':<15}"
    )
    print("  " + "-" * 75)

    creator_breakdowns = []
    for cid, imp in sorted(creator_counts.items(), key=lambda x: x[1], reverse=True):
        admin = Admin.get_or_none(Admin.id == cid)
        creator_name = (
            f"{admin.first_name} {admin.last_name}".strip()
            if admin
            else f"Admin #{cid}"
        )
        if len(creator_name) > 18:
            creator_name = creator_name[:15] + "..."

        net_payout = round((imp * creator_net_ecpm) / 1000.0, 2)
        gross_creator = round((imp * gross_ecpm) / 1000.0, 2)
        fee_creator = round(gross_creator - net_payout, 2)

        # Check bank profile
        profile = (
            CreatorPayoutProfile.select()
            .where(CreatorPayoutProfile.creator == cid)
            .first()
        )
        has_bank = bool(
            profile
            and profile.account_number
            and profile.ifsc_code
            and profile.account_holder_name
        )

        # Threshold and status resolution
        if net_payout < min_threshold:
            status = "accruing"  # Rolled over to next month
            status_desc = "accruing (< ₹500)"
        elif not has_bank:
            status = "pending_bank_details"
            status_desc = "no bank profile"
        else:
            status = "reconciled"
            status_desc = "reconciled"

        creator_breakdowns.append(
            {
                "creator_id": cid,
                "name": creator_name,
                "impressions": imp,
                "amount": net_payout,
                "gross_revenue": gross_creator,
                "platform_fee": fee_creator,
                "status": status,
            }
        )

        print(
            f"  [Creator {cid:<4}] {creator_name:<20} {imp:<13,d} ₹{net_payout:<12,.2f} {status_desc:<15}"
        )

    print("  " + "-" * 75)
    print(f"Total creator statements to generate: {len(creator_breakdowns)}")
    print("=" * 66 + "\n")

    # Confirmation
    if not auto_confirm:
        resp = input("Apply these settlements to the database? (y/N): ").strip().lower()
        if resp != "y":
            print("\n❌ Cancelled by user. Database was not modified.\n")
            sys.exit(0)

    # 5. Persist to Database atomically
    now_utc = datetime.now(timezone.utc)
    with db_proxy.atomic():
        master_rec, _ = AdPlatformMonthlyReconciliation.get_or_create(
            month=month,
            defaults={
                "total_google_revenue": gross_revenue,
                "total_impressions": total_impressions,
                "gross_ecpm": gross_ecpm,
                "platform_commission_pct": commission_pct,
                "platform_profit": platform_profit,
                "creator_pool_amount": creator_pool,
                "creator_net_ecpm": creator_net_ecpm,
                "creators_count": len(creator_breakdowns),
                "currency": settings.DEFAULT_CURRENCY,
                "status": "reconciled",
                "reconciled_at": now_utc,
            },
        )
        master_rec.total_google_revenue = gross_revenue
        master_rec.total_impressions = total_impressions
        master_rec.gross_ecpm = gross_ecpm
        master_rec.platform_commission_pct = commission_pct
        master_rec.platform_profit = platform_profit
        master_rec.creator_pool_amount = creator_pool
        master_rec.creator_net_ecpm = creator_net_ecpm
        master_rec.creators_count = len(creator_breakdowns)
        master_rec.reconciled_at = now_utc
        master_rec.status = "reconciled"
        master_rec.save()

        # Insert or update individual creator statements
        for cb in creator_breakdowns:
            stmt = (
                AdMonthlySettlement.select()
                .where(
                    AdMonthlySettlement.creator == cb["creator_id"],
                    AdMonthlySettlement.month == month,
                )
                .first()
            )
            if not stmt:
                random_hex = uuid.uuid4().hex[:4].upper()
                statement_id = (
                    f"STMT-{month.replace('-', '')}-ADM{cb['creator_id']}-{random_hex}"
                )
                stmt = AdMonthlySettlement.create(
                    reconciliation=master_rec,
                    creator_id=cb["creator_id"],
                    statement_id=statement_id,
                    month=month,
                    impressions_count=cb["impressions"],
                    ecpm=creator_net_ecpm,
                    amount=cb["amount"],
                    currency=settings.DEFAULT_CURRENCY,
                    status=cb["status"],
                    scheduled_payout_date=scheduled_payout_date,
                    gross_revenue=cb["gross_revenue"],
                    platform_commission_pct=commission_pct,
                    platform_fee=cb["platform_fee"],
                    created_at=now_utc,
                    updated_at=now_utc,
                )
            else:
                stmt.reconciliation = master_rec
                stmt.impressions_count = cb["impressions"]
                stmt.ecpm = creator_net_ecpm
                stmt.amount = cb["amount"]
                stmt.gross_revenue = cb["gross_revenue"]
                stmt.platform_fee = cb["platform_fee"]
                stmt.scheduled_payout_date = scheduled_payout_date
                if stmt.status != "paid":
                    stmt.status = cb["status"]
                stmt.updated_at = now_utc
                stmt.save()

    print(f"\n✔ SUCCESS: Monthly reconciliation for '{month}' persisted successfully!")
    print(
        f"  {len(creator_breakdowns)} statements locked. Creators can now view their finalized payouts."
    )
    print(f"  Platform profit retained: ₹{platform_profit:,.2f}\n")


def main() -> None:
    """CLI Argument Parser & Dispatcher."""
    init_db()

    parser = argparse.ArgumentParser(
        description="TalentSea Ad Monetization Monthly Reconciliation & Settlement Tool"
    )
    parser.add_argument(
        "--month",
        type=str,
        help="Billing cycle month to reconcile formatted as 'YYYY-MM' (e.g. 2026-09)",
    )
    parser.add_argument(
        "--revenue",
        type=float,
        help="Total gross ad revenue received from Google Ad Manager for the month (e.g. 50000.0)",
    )
    parser.add_argument(
        "--ecpm",
        type=float,
        help="Google gross eCPM rate for the month (e.g. 100.0)",
    )
    parser.add_argument(
        "--mark-paid",
        type=str,
        metavar="STATEMENT_ID",
        help="Mark a specific settlement statement as paid with Bank UTR",
    )
    parser.add_argument(
        "--utr",
        type=str,
        help="Official Bank UTR reference number (required when using --mark-paid)",
    )
    parser.add_argument(
        "--history",
        action="store_true",
        help="View company master revenue, 30%% profit, and creator pool balance sheet",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Bypass interactive confirmation prompt",
    )

    args = parser.parse_args()

    if args.history:
        display_history()
        return

    if args.mark_paid:
        if not args.utr:
            print(
                "\n❌ Error: --utr <UTR_CODE> is required when marking a statement as paid.\n"
            )
            sys.exit(1)
        mark_statement_paid(statement_id=args.mark_paid, utr=args.utr)
        return

    if args.month:
        reconcile_month(
            month=args.month,
            revenue=args.revenue,
            ecpm=args.ecpm,
            auto_confirm=args.yes,
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
