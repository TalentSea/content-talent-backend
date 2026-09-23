from fastapi import APIRouter, Query, status

from app.dependencies import CurrentSuperAdmin
from app.schemas.admin.tenant_schemas import (
    TenantCreateRequest,
    TenantCreateResponse,
    TenantListItem,
    TenantResponse,
    TenantStatusUpdateRequest,
)
from app.schemas.shared.common_schemas import PaginatedResponse
from app.services.admin.tenant_service import TenantService

router = APIRouter(prefix="/api/v1/admin/tenants", tags=["Super Admin Tenants"])
tenant_service = TenantService()


@router.get(
    "",
    response_model=PaginatedResponse[TenantResponse] | list[TenantListItem],
    status_code=status.HTTP_200_OK,
)
def list_tenants(
    current_super_admin: CurrentSuperAdmin,
    mode: str = Query(
        "compact",
        description="Response mode: 'compact' (flat list) or 'detailed' (paginated full details)",
    ),
    page: int = Query(1, ge=1, description="Page number (only used in detailed mode)"),
    limit: int = Query(
        20, ge=1, le=100, description="Items per page (only used in detailed mode)"
    ),
    is_active: bool | None = Query(
        None, description="Filter by active status (true/false)"
    ),
    search: str | None = Query(None, description="Filter by tenant name substring"),
):
    """
    GET /api/v1/admin/tenants — List all platform studio tenants for selection and management (Super Admin only).
    """
    return tenant_service.list_tenants(
        mode=mode,
        page=page,
        limit=limit,
        is_active=is_active,
        search=search,
    )


@router.post(
    "", response_model=TenantCreateResponse, status_code=status.HTTP_201_CREATED
)
def create_tenant(
    payload: TenantCreateRequest,
    current_super_admin: CurrentSuperAdmin,
):
    """
    POST /api/v1/admin/tenants — Provision a new brand/tenant, owner admin, and default plans (Super Admin only).
    """
    return tenant_service.create_tenant(payload)


@router.get(
    "/{tenant_id}", response_model=TenantResponse, status_code=status.HTTP_200_OK
)
def get_tenant_details(
    tenant_id: int,
    current_super_admin: CurrentSuperAdmin,
):
    """
    GET /api/v1/admin/tenants/{tenant_id} — Retrieve tenant studio details and metrics (Super Admin only).
    """
    return tenant_service.get_tenant(tenant_id)


@router.patch(
    "/{tenant_id}/status", response_model=TenantResponse, status_code=status.HTTP_200_OK
)
def update_tenant_status(
    tenant_id: int,
    payload: TenantStatusUpdateRequest,
    current_super_admin: CurrentSuperAdmin,
):
    """
    PATCH /api/v1/admin/tenants/{tenant_id}/status — Activate/deactivate tenant (Super Admin only).
    """
    return tenant_service.update_tenant_status(tenant_id, payload)
