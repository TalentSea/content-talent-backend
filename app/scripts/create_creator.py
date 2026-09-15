import argparse
import getpass
import re
import sys

from peewee import fn

from app.database import db_proxy, init_db
from app.models.admin import Admin
from app.models.branding import Branding
from app.models.subscription_plan import SubscriptionPlan
from app.utils.auth import hash_password

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email_format(email: str) -> bool:
    """Validates email format using regex."""
    return bool(EMAIL_REGEX.match(email.strip()))


def provision_creator(
    email: str,
    password: str,
    first_name: str | None = None,
    last_name: str | None = None,
    studio_name: str | None = None,
) -> dict:
    """
    Atomically provisions a new Creator Admin, Studio Branding identity, and two default subscription plans.
    """
    clean_email = email.strip().lower()

    if not validate_email_format(clean_email):
        raise ValueError(f"Invalid email address format: '{email}'")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")

    # Determine default studio name if omitted
    name_parts = [p for p in (first_name, last_name) if p]
    if not studio_name:
        if name_parts:
            studio_name = f"{' '.join(name_parts)} Studio"
        else:
            studio_name = "Creator Studio"

    # Ensure database is initialized and connected
    init_db()
    if db_proxy.is_closed():
        db_proxy.connect()

    # Check for existing email conflict
    existing_admin = Admin.get_or_none(fn.LOWER(Admin.email) == clean_email)
    if existing_admin:
        raise ValueError(
            f"Admin with email '{clean_email}' already exists (ID: {existing_admin.id})"
        )

    # Hash password using PBKDF2-HMAC-SHA256 (600,000 iterations)
    password_hash = hash_password(password)

    with db_proxy.atomic():
        # 1. Create Admin
        admin = Admin.create(
            email=clean_email,
            password_hash=password_hash,
            first_name=first_name.strip() if first_name else None,
            last_name=last_name.strip() if last_name else None,
        )

        # 2. Create 1:1 Branding
        branding = Branding.create(
            user=admin.id,
            studio_name=studio_name.strip(),
        )

        # 3. Create 2 Fixed Subscription Plans
        plan_with_ads = SubscriptionPlan.create(
            user=admin.id,
            plan_type="with_ads",
            name="Standard with Ads",
            description="Access to our full catalog with occasional commercial breaks.",
            base_price=99.0,
            discount_percentage=0.0,
            final_price=99.0,
            currency="INR",
            billing_period_value=1,
            billing_period_unit="months",
            badge_text="Popular",
            display_order=1,
        )

        plan_no_ads = SubscriptionPlan.create(
            user=admin.id,
            plan_type="no_ads",
            name="Premium Ad-Free",
            description="Unlimited streaming with zero ads and maximum quality.",
            base_price=199.0,
            discount_percentage=0.0,
            final_price=199.0,
            currency="INR",
            billing_period_value=1,
            billing_period_unit="months",
            badge_text="Best Value",
            display_order=2,
        )

    return {
        "admin_id": admin.id,
        "email": admin.email,
        "first_name": admin.first_name,
        "last_name": admin.last_name,
        "studio_name": branding.studio_name,
        "plans": [
            {
                "id": plan_with_ads.id,
                "name": plan_with_ads.name,
                "price": plan_with_ads.final_price,
            },
            {
                "id": plan_no_ads.id,
                "name": plan_no_ads.name,
                "price": plan_no_ads.final_price,
            },
        ],
    }


def main():
    """CLI entrypoint for creator provisioning."""
    parser = argparse.ArgumentParser(
        description="Atomically provision a new Creator Admin, Studio Branding, and Two Subscription Plans."
    )
    parser.add_argument(
        "--email", required=True, help="Creator login email address (required)"
    )
    parser.add_argument(
        "--password",
        required=False,
        default=None,
        help="Initial account password (min 8 chars)",
    )
    parser.add_argument(
        "--first-name", required=False, default=None, help="Creator first name"
    )
    parser.add_argument(
        "--last-name", required=False, default=None, help="Creator last name"
    )
    parser.add_argument(
        "--studio-name",
        required=False,
        default=None,
        help="Studio / channel brand name",
    )

    args = parser.parse_args()

    password = args.password
    if not password:
        # Prompt interactively with hidden input
        password = getpass.getpass("Enter creator password (min 8 chars): ")
        password_confirm = getpass.getpass("Confirm creator password: ")
        if password != password_confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    try:
        result = provision_creator(
            email=args.email,
            password=password,
            first_name=args.first_name,
            last_name=args.last_name,
            studio_name=args.studio_name,
        )

        print("\n==================================================")
        print("  CREATOR ONBOARDING SUCCESSFUL")
        print("==================================================")
        print(f"  Admin ID:      {result['admin_id']}")
        print(f"  Email:         {result['email']}")
        print(f"  Studio Name:   {result['studio_name']}")
        print(
            f"  Creator Name:  {result['first_name'] or ''} {result['last_name'] or ''}".strip()
        )
        print("  Subscription Plans Provisioned:")
        for plan in result["plans"]:
            print(f"    - [{plan['id']}] {plan['name']} (₹{plan['price']:.0f}/month)")
        print("==================================================\n")

    except ValueError as e:
        print(f"\nError: {e}\n", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"\nUnexpected system error during provisioning: {e}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
