import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from peewee import fn

from app.database import db_proxy, init_db
from app.models.admin import Admin
from app.models.branding import Branding


def format_table(rows: list[list[str]], headers: list[str]) -> str:
    """Formats console rows into an ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    data_lines = [
        " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row))
        for row in rows
    ]
    return f"{header_line}\n{separator}\n" + "\n".join(data_lines)


def list_creators():
    """Lists all creators registered on the platform with their active status and deactivation reason."""
    init_db()
    if db_proxy.is_closed():
        db_proxy.connect()

    admins = list(Admin.select().order_by(Admin.id.asc()))
    if not admins:
        print("\n[INFO] No creators found in database.\n")
        return

    rows = []
    for a in admins:
        branding = Branding.get_or_none(Branding.user == a.id)
        studio = branding.studio_name if branding and branding.studio_name else "N/A"
        is_active = getattr(a, "is_active", True)
        status_str = "ACTIVE" if is_active else "DEACTIVATED"
        reason_str = (
            getattr(a, "deactivation_reason", None) or "-"
            if not is_active
            else "-"
        )
        rows.append([str(a.id), a.email, a.name, studio, status_str, reason_str])

    print("\n==========================================================================================")
    print("                              TALENTSEA CREATOR ACCOUNTS                                  ")
    print("==========================================================================================\n")
    print(format_table(rows, ["ID", "Email", "Name", "Studio", "Status", "Deactivation Reason"]))
    print("\n")


def get_admin_by_identifier(
    email: str | None = None, admin_id: int | None = None
) -> Admin | None:
    """Fetches an Admin by either email or numeric ID."""
    if admin_id:
        return Admin.get_or_none(Admin.id == admin_id)
    if email:
        return Admin.get_or_none(fn.LOWER(Admin.email) == email.strip().lower())
    return None


def deactivate_creator(
    email: str | None = None, admin_id: int | None = None, reason: str | None = None
):
    """Deactivates a creator account, stores the deactivation reason, revokes active refresh sessions, and suspends ad monetization."""
    init_db()
    if db_proxy.is_closed():
        db_proxy.connect()

    admin = get_admin_by_identifier(email=email, admin_id=admin_id)
    if not admin:
        print(
            f"\n[ERROR] Creator not found for {'ID ' + str(admin_id) if admin_id else 'email ' + str(email)}.\n"
        )
        sys.exit(1)

    if not getattr(admin, "is_active", True):
        print(
            f"\n[INFO] Creator '{admin.email}' (ID: {admin.id}) is ALREADY deactivated."
        )
        if getattr(admin, "deactivation_reason", None):
            print(f"  Existing Reason: {admin.deactivation_reason}")
        print("\n")
        return

    now_utc = datetime.now(timezone.utc)
    deact_reason = reason.strip() if reason and reason.strip() else "Administrative deactivation"

    admin.is_active = False
    admin.deactivation_reason = deact_reason
    admin.deactivated_at = now_utc
    admin.refresh_token = None  # Invalidate session immediately
    admin.updated_at = now_utc
    admin.save()

    print("\n=======================================================")
    print("           CREATOR ACCOUNT DEACTIVATED                ")
    print("=======================================================")
    print(f"  Creator ID:          {admin.id}")
    print(f"  Email:               {admin.email}")
    print(f"  Name:                {admin.name}")
    print("  Status:              DEACTIVATED")
    print(f"  Deactivation Reason: {admin.deactivation_reason}")
    print(f"  Deactivated At:      {admin.deactivated_at.isoformat()}")
    print("  Sessions:            REVOKED (Refresh token cleared)")
    print("  Ad Monetization:     SUSPENDED")
    print("=======================================================\n")


def activate_creator(email: str | None = None, admin_id: int | None = None):
    """Re-activates a creator account, clears the deactivation reason, and allows login and ad impression monetization."""
    init_db()
    if db_proxy.is_closed():
        db_proxy.connect()

    admin = get_admin_by_identifier(email=email, admin_id=admin_id)
    if not admin:
        print(
            f"\n[ERROR] Creator not found for {'ID ' + str(admin_id) if admin_id else 'email ' + str(email)}.\n"
        )
        sys.exit(1)

    if getattr(admin, "is_active", True):
        print(f"\n[INFO] Creator '{admin.email}' (ID: {admin.id}) is ALREADY active.\n")
        return

    now_utc = datetime.now(timezone.utc)
    admin.is_active = True
    admin.deactivation_reason = None
    admin.deactivated_at = None
    admin.updated_at = now_utc
    admin.save()

    print("\n=======================================================")
    print("            CREATOR ACCOUNT ACTIVATED                  ")
    print("=======================================================")
    print(f"  Creator ID:      {admin.id}")
    print(f"  Email:           {admin.email}")
    print(f"  Name:            {admin.name}")
    print("  Status:          ACTIVE")
    print("  Reason Cleared:  YES")
    print("  Ad Monetization: RESUMED")
    print("=======================================================\n")


def show_status(email: str | None = None, admin_id: int | None = None):
    """Inspects detailed status and deactivation audit history of a single creator."""
    init_db()
    if db_proxy.is_closed():
        db_proxy.connect()

    admin = get_admin_by_identifier(email=email, admin_id=admin_id)
    if not admin:
        print(
            f"\n[ERROR] Creator not found for {'ID ' + str(admin_id) if admin_id else 'email ' + str(email)}.\n"
        )
        sys.exit(1)

    branding = Branding.get_or_none(Branding.user == admin.id)
    studio = branding.studio_name if branding and branding.studio_name else "N/A"
    is_active = getattr(admin, "is_active", True)
    status_str = "ACTIVE" if is_active else "DEACTIVATED"

    print("\n=======================================================")
    print("            CREATOR ACCOUNT DETAILS                    ")
    print("=======================================================")
    print(f"  ID:                  {admin.id}")
    print(f"  Email:               {admin.email}")
    print(f"  Name:                {admin.name}")
    print(f"  Studio:              {studio}")
    print(f"  Status:              {status_str}")
    if not is_active:
        print(f"  Deactivation Reason: {admin.deactivation_reason or 'None'}")
        print(f"  Deactivated At:      {admin.deactivated_at or 'N/A'}")
    print(f"  Created At:          {admin.created_at}")
    print(f"  Updated At:          {admin.updated_at}")
    print("=======================================================\n")


def main():
    parser = argparse.ArgumentParser(
        description="Platform CLI Tool to manage creator activation status (TalentSea OTT)."
    )
    subparsers = parser.add_subparsers(dest="action", help="Action to perform")

    # List action
    subparsers.add_parser(
        "list", help="List all creators and their current active status"
    )

    # Deactivate action
    deact_parser = subparsers.add_parser(
        "deactivate", help="Deactivate a creator account"
    )
    deact_group = deact_parser.add_mutually_exclusive_group(required=True)
    deact_group.add_argument("--email", "-e", type=str, help="Creator email address")
    deact_group.add_argument("--id", "-i", type=int, help="Creator numeric database ID")
    deact_parser.add_argument(
        "--reason", "-r", type=str, default=None, help="Reason for deactivation"
    )

    # Activate action
    act_parser = subparsers.add_parser("activate", help="Reactivate a creator account")
    act_group = act_parser.add_mutually_exclusive_group(required=True)
    act_group.add_argument("--email", "-e", type=str, help="Creator email address")
    act_group.add_argument("--id", "-i", type=int, help="Creator numeric database ID")

    # Status action
    stat_parser = subparsers.add_parser(
        "status", help="Show detailed status for a creator"
    )
    stat_group = stat_parser.add_mutually_exclusive_group(required=True)
    stat_group.add_argument("--email", "-e", type=str, help="Creator email address")
    stat_group.add_argument("--id", "-i", type=int, help="Creator numeric database ID")

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(0)

    if args.action == "list":
        list_creators()
    elif args.action == "deactivate":
        deactivate_creator(email=args.email, admin_id=args.id, reason=args.reason)
    elif args.action == "activate":
        activate_creator(email=args.email, admin_id=args.id)
    elif args.action == "status":
        show_status(email=args.email, admin_id=args.id)


if __name__ == "__main__":
    main()
