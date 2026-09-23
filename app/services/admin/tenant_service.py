import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.config import get_settings
from app.database import db_proxy
from app.models.subscription_plan import SubscriptionPlan
from app.models.tenant import Tenant
from app.repositories.admin.tenant_repository import TenantRepository
from app.schemas.admin.tenant_schemas import (
    AdminUserCreateRequest,
    AdminUserResponse,
    TenantCreateRequest,
    TenantCreateResponse,
    TenantListItem,
    TenantResponse,
    TenantStatusUpdateRequest,
)
from app.schemas.shared.common_schemas import PaginatedResponse
from app.utils.auth import hash_password
from app.utils.string_utils import slugify

logger = logging.getLogger(__name__)


class TenantService:
    """
    Business service layer for Tenant and Multi-Tenant Admin user management.
    """

    def __init__(self, repo: TenantRepository | None = None):
        self.repo = repo or TenantRepository()

    def _to_tenant_response(
        self, tenant, counts: dict[str, int] | None = None
    ) -> TenantResponse:
        if counts is None:
            counts = self.repo.get_counts(tenant.id)
        return TenantResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            tagline=tenant.tagline,
            description=tenant.description,
            is_active=tenant.is_active,
            logo_url=tenant.logo_url,
            deactivation_reason=tenant.deactivation_reason,
            deactivated_at=tenant.deactivated_at,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
            admins_count=counts.get("admins_count", 0),
            videos_count=counts.get("videos_count", 0),
            subscribers_count=counts.get("subscribers_count", 0),
        )

    def _to_admin_response(self, admin) -> AdminUserResponse:
        return AdminUserResponse(
            id=admin.id,
            email=admin.email,
            first_name=admin.first_name,
            last_name=admin.last_name,
            phone=admin.phone,
            role=admin.role,
            is_owner=admin.is_owner,
            is_active=admin.is_active,
            avatar_url=admin.avatar_url,
            created_at=admin.created_at,
        )

    def create_tenant(self, payload: TenantCreateRequest) -> TenantCreateResponse:
        """
        Atomically provisions a new Tenant brand, initial owner Admin, and default Subscription Plans.
        """
        existing_tenant = self.repo.get_tenant_by_name(payload.name)
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant with brand name '{payload.name}' already exists",
            )

        derived_slug = slugify(payload.name)
        if Tenant.select().where(Tenant.slug == derived_slug).exists():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tenant with slug '{derived_slug}' already exists",
            )

        existing_admin = self.repo.get_admin_by_email(payload.admin_email)
        if existing_admin:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Admin with email '{payload.admin_email}' already exists",
            )

        password_hash = hash_password(payload.admin_password)

        with db_proxy.atomic():
            # 1. Create Tenant
            tenant = self.repo.create_tenant(
                name=payload.name,
                tagline=payload.tagline,
                description=payload.description,
            )

            # 2. Create Owner Admin
            admin = self.repo.create_admin(
                tenant_id=tenant.id,
                email=payload.admin_email,
                password_hash=password_hash,
                first_name=payload.admin_first_name,
                last_name=payload.admin_last_name,
                phone=payload.admin_phone,
                is_owner=True,
            )

            # 3. Provision Default Subscription Plans
            settings = get_settings()
            SubscriptionPlan.create(
                tenant=tenant.id,
                plan_type="with_ads",
                name="Standard with Ads",
                description="Access to full catalog with occasional commercial breaks.",
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
                tenant=tenant.id,
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

        return TenantCreateResponse(
            id=tenant.id,
            owner_id=admin.id,
            name=tenant.name,
            slug=tenant.slug,
            tagline=tenant.tagline,
            description=tenant.description,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
        )

    def list_tenants(
        self,
        mode: str = "compact",
        page: int = 1,
        limit: int = 20,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[TenantResponse] | list[TenantListItem]:
        """
        Lists tenants based on mode. 'compact' returns a flat list for dropdowns.
        'detailed' returns a paginated list with full metrics for management tables.
        """
        is_detailed = mode == "detailed"

        # 1. Fetch data (applying pagination only if detailed; selects all columns if detailed)
        tenants = self.repo.list_tenants(
            is_active=is_active,
            search=search,
            page=page if is_detailed else None,
            limit=limit if is_detailed else None,
            detailed=is_detailed,
        )

        # 2. Format detailed paginated response with batch aggregated counts
        if is_detailed:
            total = self.repo.count_tenants(is_active=is_active, search=search)
            tenant_ids = [t.id for t in tenants]
            batch_counts = self.repo.get_batch_counts(tenant_ids)
            items = [
                self._to_tenant_response(t, batch_counts.get(t.id)) for t in tenants
            ]
            return PaginatedResponse.create(
                items=items, total=total, page=page, limit=limit
            )

        # 3. Format compact dropdown response
        return [
            TenantListItem(id=t.id, name=t.name, is_active=t.is_active) for t in tenants
        ]

    def get_tenant(self, tenant_id: int) -> TenantResponse:
        """
        Retrieves details and operational metrics for a specific tenant.
        """
        tenant = self.repo.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )
        return self._to_tenant_response(tenant)

    def update_tenant_status(
        self, tenant_id: int, payload: TenantStatusUpdateRequest
    ) -> TenantResponse:
        """
        Updates activation status for a tenant.
        """
        tenant = self.repo.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )

        updates = payload.model_dump(exclude_unset=True)
        if not updates["is_active"]:
            updates["deactivated_at"] = datetime.now(timezone.utc)
        else:
            updates["deactivated_at"] = None
            updates["deactivation_reason"] = None

        updated = self.repo.update_tenant(tenant_id, updates)
        return self._to_tenant_response(updated)

    def list_tenant_admins(self, tenant_id: int) -> list[AdminUserResponse]:
        """
        Lists all admin users belonging to a tenant.
        """
        admins = self.repo.list_admins_by_tenant(tenant_id)
        return [self._to_admin_response(a) for a in admins]

    def create_tenant_admin(
        self, tenant_id: int, payload: AdminUserCreateRequest
    ) -> AdminUserResponse:
        """
        Invites/creates a new admin user under the specified tenant.
        """
        tenant = self.repo.get_tenant_by_id(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )

        existing = self.repo.get_admin_by_email(payload.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Admin with email '{payload.email}' already exists",
            )

        password_hash = hash_password(payload.password)
        admin = self.repo.create_admin(
            tenant_id=tenant_id,
            email=payload.email,
            password_hash=password_hash,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            is_owner=False,
        )
        return self._to_admin_response(admin)

    def update_admin_status(
        self, tenant_id: int, admin_id: int, is_active: bool
    ) -> AdminUserResponse:
        """
        Activates or suspends an admin user under a tenant.
        """
        admin = self.repo.get_admin_by_id_and_tenant(admin_id, tenant_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin {admin_id} not found under tenant {tenant_id}",
            )

        if admin.is_owner and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate the tenant primary owner account",
            )

        updated = self.repo.update_admin_status(admin, is_active)
        return self._to_admin_response(updated)

    def delete_tenant_admin(self, tenant_id: int, admin_id: int) -> None:
        """
        Permanently removes a staff administrator account from the tenant.
        Safety Rule: Tenant owners (is_owner == True) cannot be deleted.
        """
        admin = self.repo.get_admin_by_id_and_tenant(admin_id, tenant_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Admin {admin_id} not found under tenant {tenant_id}",
            )

        if admin.is_owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the tenant owner account",
            )

        self.repo.delete_admin(admin)

