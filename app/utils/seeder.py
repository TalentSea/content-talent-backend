import logging

from peewee import fn

from app.config import get_settings
from app.database import db_proxy
from app.models.admin import Admin
from app.models.subscription_plan import SubscriptionPlan
from app.models.tenant import Tenant
from app.utils.auth import hash_password

logger = logging.getLogger(__name__)


def seed_super_admin() -> Admin:
    """
    Idempotent startup seeding function that provisions the initial Platform Super Admin account if none exists.
    Configured via SUPER_ADMIN_EMAIL and SUPER_ADMIN_PASSWORD environment variables.
    """
    settings = get_settings()
    email = settings.SUPER_ADMIN_EMAIL.strip().lower()

    if db_proxy.is_closed():
        db_proxy.connect()

    try:
        existing = Admin.get_or_none(
            (fn.LOWER(Admin.email) == email) | (Admin.role == "super_admin")
        )
        if existing:
            return existing

        password_hash = hash_password(settings.SUPER_ADMIN_PASSWORD)
        super_admin = Admin.create(
            tenant=None,
            role="super_admin",
            is_owner=False,
            email=email,
            password_hash=password_hash,
            first_name="Super",
            last_name="Admin",
            is_active=True,
        )
        logger.info("Successfully provisioned Platform Super Admin: %s", email)
        return super_admin
    except Exception as e:
        logger.error("Failed to seed Super Admin: %s", e)
        raise


def seed_default_tenant() -> Tenant | None:
    """
    Provisions a default initial tenant studio and owner admin account if the database contains zero tenants.
    Enables immediate local development and testing without requiring manual GUI provisioning on first run.
    """
    if db_proxy.is_closed():
        db_proxy.connect()

    try:
        if Tenant.select().count() > 0:
            return None

        with db_proxy.atomic():
            tenant = Tenant.create(
                name="Content Talent",
                slug="content-talent",
                tagline="Official Talent Studio",
                description="The flagship creator studio and entertainment network.",
                is_active=True,
            )

            password_hash = hash_password("Admin@1234")
            Admin.create(
                tenant=tenant,
                role="admin",
                is_owner=True,
                email="jakkamadhu046@gmail.com",
                password_hash=password_hash,
                first_name="Madhu",
                last_name="Jakka",
                is_active=True,
            )

            # Provision default subscription tiers
            settings = get_settings()
            SubscriptionPlan.create(
                tenant=tenant,
                plan_type="with_ads",
                name="Standard with Ads",
                description="Access to our full catalog with occasional commercial breaks.",
                base_price=99.0,
                discount_percentage=0.0,
                final_price=99.0,
                currency=settings.DEFAULT_CURRENCY,
                billing_period_value=1,
                billing_period_unit="months",
                badge_text="Popular",
                display_order=1,
            )

            SubscriptionPlan.create(
                tenant=tenant,
                plan_type="no_ads",
                name="Premium Ad-Free",
                description="Unlimited streaming with zero ads and maximum quality.",
                base_price=199.0,
                discount_percentage=0.0,
                final_price=199.0,
                currency=settings.DEFAULT_CURRENCY,
                billing_period_value=1,
                billing_period_unit="months",
                badge_text="Best Value",
                display_order=2,
            )

        logger.info("Successfully provisioned default initial tenant: %s", tenant.name)
        return tenant
    except Exception as e:  # noqa: BLE001
        logger.error("Failed to seed default tenant: %s", e)
        return None
