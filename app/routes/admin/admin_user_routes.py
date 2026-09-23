from fastapi import APIRouter, HTTPException, status

from app.dependencies import CurrentAdmin
from app.schemas.admin.tenant_schemas import (
    AdminUserCreateRequest,
    AdminUserResponse,
    AdminUserStatusUpdateRequest,
)
from app.services.admin.tenant_service import TenantService

router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin Users"])
tenant_service = TenantService()


def _ensure_owner_or_super_admin(current_user: dict):
    if not (current_user.get("is_owner") or current_user.get("role") == "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the tenant owner or a super admin can manage admin users.",
        )


@router.get("", response_model=list[AdminUserResponse], status_code=status.HTTP_200_OK)
def list_admins(current_user: CurrentAdmin):
    """
    GET /api/v1/admin/users — List all admin users in the active tenant.
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active tenant context found.",
        )
    return tenant_service.list_tenant_admins(tenant_id)


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminUserCreateRequest,
    current_user: CurrentAdmin,
):
    """
    POST /api/v1/admin/users — Invite or add a new admin user to the active tenant.
    """
    _ensure_owner_or_super_admin(current_user)
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active tenant context found.",
        )
    return tenant_service.create_tenant_admin(tenant_id, payload)


@router.patch("/{admin_id}/status", response_model=AdminUserResponse, status_code=status.HTTP_200_OK)
def update_admin_status(
    admin_id: int,
    payload: AdminUserStatusUpdateRequest,
    current_user: CurrentAdmin,
):
    """
    PATCH /api/v1/admin/users/{admin_id}/status — Activate or suspend an admin user.
    """
    _ensure_owner_or_super_admin(current_user)
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active tenant context found.",
        )
    return tenant_service.update_admin_status(tenant_id, admin_id, payload.is_active)


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_admin(
    admin_id: int,
    current_user: CurrentAdmin,
):
    """
    DELETE /api/v1/admin/users/{admin_id} — Permanently remove a staff administrator account from the tenant.
    """
    _ensure_owner_or_super_admin(current_user)
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active tenant context found.",
        )
    tenant_service.delete_tenant_admin(tenant_id, admin_id)

