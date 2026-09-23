from datetime import datetime, timezone
from typing import Any

from app.models.tenant import Tenant
from app.utils.string_utils import slugify


class BrandingRepository:
    """
    Data access repository for Tenant Branding and Studio Identity (stored directly on Tenant model).
    """

    def get_by_tenant_id(self, tenant_id: int) -> Tenant | None:
        """
        Retrieves the tenant record by tenant_id.
        """
        return Tenant.get_or_none(Tenant.id == tenant_id)

    def get_by_user_id(self, tenant_id: int) -> Tenant | None:
        """
        Backward-compatible alias: in the new architecture, tenant_id is passed.
        """
        return self.get_by_tenant_id(tenant_id)

    def update_branding_text(self, tenant_id: int, fields: dict[str, Any]) -> Tenant:
        """
        Applies partial updates to tenant brand text fields.
        Maps 'studio_name' to 'Tenant.name' and updates 'Tenant.slug'.
        """
        tenant = self.get_by_tenant_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        if "studio_name" in fields and fields["studio_name"] is not None:
            new_name = fields["studio_name"].strip()
            if new_name:
                tenant.name = new_name
                tenant.slug = slugify(new_name)
        if "tagline" in fields:
            tenant.tagline = fields["tagline"].strip() if fields["tagline"] else None
        if "description" in fields:
            tenant.description = (
                fields["description"].strip() if fields["description"] else None
            )

        tenant.updated_at = datetime.now(timezone.utc)
        tenant.save()
        return tenant

    def update_logo_url(self, tenant_id: int, logo_url: str) -> Tenant:
        """
        Updates the tenant logo_url and updated_at timestamp.
        """
        tenant = self.get_by_tenant_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        tenant.logo_url = logo_url
        tenant.updated_at = datetime.now(timezone.utc)
        tenant.save()
        return tenant

    def update_banner_url(self, tenant_id: int, banner_url: str) -> Tenant:
        """
        Updates the tenant banner_url and updated_at timestamp.
        """
        tenant = self.get_by_tenant_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        tenant.banner_url = banner_url
        tenant.updated_at = datetime.now(timezone.utc)
        tenant.save()
        return tenant
