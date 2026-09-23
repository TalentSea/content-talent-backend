from datetime import datetime, timezone
from typing import Any

from peewee import fn

from app.models.admin import Admin
from app.models.subscriber import Subscriber
from app.models.tenant import Tenant
from app.models.video import Video


class TenantRepository:
    """
    Data access repository for Tenant and Tenant Admin entities.
    """

    def list_tenants(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        page: int | None = None,
        limit: int | None = None,
    ) -> list[Tenant]:
        """
        Retrieves all tenants with optional is_active and name filtering.
        Supports pagination via page and limit.
        """
        query = Tenant.select(Tenant.id, Tenant.name, Tenant.is_active).order_by(
            Tenant.id.asc()
        )
        if is_active is not None:
            query = query.where(Tenant.is_active == is_active)
        if search and search.strip():
            query = query.where(fn.LOWER(Tenant.name).contains(search.strip().lower()))

        if page is not None and limit is not None:
            query = query.paginate(page, limit)

        return list(query)

    def count_tenants(
        self,
        is_active: bool | None = None,
        search: str | None = None,
    ) -> int:
        """
        Counts total tenants matching the filters for pagination.
        """
        query = Tenant.select(Tenant.id)
        if is_active is not None:
            query = query.where(Tenant.is_active == is_active)
        if search and search.strip():
            query = query.where(fn.LOWER(Tenant.name).contains(search.strip().lower()))
        return query.count()

    def get_tenant_by_id(self, tenant_id: int) -> Tenant | None:
        """
        Retrieves a tenant by primary key ID.
        """
        return Tenant.get_or_none(Tenant.id == tenant_id)

    def get_tenant_by_name(self, name: str) -> Tenant | None:
        """
        Retrieves a tenant by case-insensitive name match.
        """
        return Tenant.get_or_none(fn.LOWER(Tenant.name) == name.strip().lower())

    def create_tenant(
        self,
        name: str,
        tagline: str | None = None,
        description: str | None = None,
    ) -> Tenant:
        """
        Creates and persists a new Tenant entity.
        """
        return Tenant.create(
            name=name.strip(),
            tagline=tagline.strip() if tagline else None,
            description=description.strip() if description else None,
        )

    def update_tenant(self, tenant_id: int, fields: dict[str, Any]) -> Tenant:
        """
        Applies partial updates to a tenant.
        """
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        for key, value in fields.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        tenant.updated_at = datetime.now(timezone.utc)
        tenant.save()
        return tenant

    def get_counts(self, tenant_id: int) -> dict[str, int]:
        """
        Fetches operational stats (admins, videos, subscribers) for a tenant.
        """
        admins_count = Admin.select().where(Admin.tenant == tenant_id).count()
        videos_count = Video.select().where(Video.tenant == tenant_id).count()
        subscribers_count = (
            Subscriber.select().where(Subscriber.tenant == tenant_id).count()
        )
        return {
            "admins_count": admins_count,
            "videos_count": videos_count,
            "subscribers_count": subscribers_count,
        }

    def list_admins_by_tenant(self, tenant_id: int) -> list[Admin]:
        """
        Lists all admin users belonging to a specific tenant.
        """
        return list(
            Admin.select().where(Admin.tenant == tenant_id).order_by(Admin.id.asc())
        )

    def get_admin_by_id_and_tenant(
        self, admin_id: int, tenant_id: int | None = None
    ) -> Admin | None:
        """
        Retrieves an admin by ID, optionally verifying tenant assignment.
        """
        if tenant_id is not None:
            return Admin.get_or_none(
                (Admin.id == admin_id) & (Admin.tenant == tenant_id)
            )
        return Admin.get_or_none(Admin.id == admin_id)

    def get_admin_by_email(self, email: str) -> Admin | None:
        """
        Retrieves an admin by case-insensitive email.
        """
        return Admin.get_or_none(fn.LOWER(Admin.email) == email.strip().lower())

    def create_admin(
        self,
        tenant_id: int,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        phone: str | None = None,
        is_owner: bool = False,
    ) -> Admin:
        """
        Creates an admin user account bound to a tenant.
        """
        return Admin.create(
            tenant=tenant_id,
            email=email.strip().lower(),
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip() if phone else None,
            role="admin",
            is_owner=is_owner,
            is_active=True,
        )

    def update_admin_status(
        self, admin_or_id: Admin | int, is_active: bool, tenant_id: int | None = None
    ) -> Admin:
        """
        Activates or suspends an admin user account.
        Accepts either an already fetched Admin instance (avoiding redundant DB queries)
        or an integer admin_id scoped to tenant_id.
        """
        if isinstance(admin_or_id, Admin):
            admin = admin_or_id
        else:
            admin = self.get_admin_by_id_and_tenant(admin_or_id, tenant_id)
            if not admin:
                raise ValueError(f"Admin {admin_or_id} not found")
        admin.is_active = is_active
        admin.updated_at = datetime.now(timezone.utc)
        admin.save()
        return admin

    def delete_admin(
        self, admin_or_id: Admin | int, tenant_id: int | None = None
    ) -> bool:
        """
        Permanently deletes an admin user account scoped to a tenant.
        """
        if isinstance(admin_or_id, Admin):
            admin = admin_or_id
        else:
            admin = self.get_admin_by_id_and_tenant(admin_or_id, tenant_id)
            if not admin:
                return False
        admin.delete_instance()
        return True

