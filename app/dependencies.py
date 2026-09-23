from typing import Annotated, Any

from fastapi import Cookie, Depends, File, Header, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordBearer

from app.models.admin import Admin
from app.models.subscriber import Subscriber
from app.models.tenant import Tenant
from app.utils.auth import decode_access_token, verify_tenant_active

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/admin/auth/login", auto_error=False
)


def get_current_subscriber(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict[str, Any]:
    """
    Guards Mobile API routes (/api/v1/mobile/*) to ensure caller is strictly a Mobile Subscriber or Guest.
    """
    payload = decode_access_token(token)

    # Reject non-subscriber tokens (e.g. admin credentials) on mobile routes
    token_role = payload.get("role")
    if token_role not in ("subscriber", "guest"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Mobile subscriber credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["user_id"]

    # Validate strictly against Subscriber table
    sub = Subscriber.get_or_none(Subscriber.id == user_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated subscriber account no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not sub.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscriber account is disabled",
        )

    verify_tenant_active(sub.tenant)

    return {
        "user_id": sub.id,
        "tenant_id": sub.tenant_id,
        "role": sub.role,
    }


def get_optional_subscriber(
    token: Annotated[str | None, Depends(oauth2_scheme_optional)] = None,
) -> dict[str, Any] | None:
    """
    Optional authentication for endpoints that allow guest access or guest account upgrade.
    """
    if not token:
        return None
    try:
        return get_current_subscriber(token)
    except HTTPException:
        return None


def get_current_admin(
    cookie_token: Annotated[str | None, Cookie(alias="admin_access_token")] = None,
    header_token: Annotated[str | None, Depends(oauth2_scheme_optional)] = None,
    x_tenant_id: Annotated[int | None, Header(alias="X-Tenant-Id")] = None,
) -> dict[str, Any]:
    """
    Guards Admin Web Portal routes (/api/v1/admin/*) to ensure the caller is an Admin or Super Admin.
    Extracts admin user_id and active tenant_id from context.
    - Super Admin: resolves tenant_id from 'X-Tenant-Id' header, or defaults to the first provisioned Tenant.
    - Tenant Admin: resolves tenant_id from admin's assigned Tenant record and enforces tenant active check.
    Prioritizes HttpOnly cookie; falls back to Bearer header for Swagger/Postman API tooling.
    """
    token = cookie_token or header_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: No access token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)

    token_role = payload.get("role")
    if token_role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin portal authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["user_id"]

    # Validate strictly against Admin table
    admin = Admin.get_or_none(Admin.id == user_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin portal authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account has been deactivated. Please contact platform administration.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Resolve active tenant context
    if admin.role == "super_admin":
        if x_tenant_id is not None:
            tenant = Tenant.get_or_none(Tenant.id == x_tenant_id)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant specified in X-Tenant-Id ({x_tenant_id}) was not found",
                )
            resolved_tenant_id = tenant.id
        else:
            # Fallback to the first tenant by default
            first_tenant = Tenant.select().order_by(Tenant.id.asc()).first()
            resolved_tenant_id = first_tenant.id if first_tenant else None
    else:
        # Tenant Admin must belong to an active tenant
        if not admin.tenant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin is not assigned to any tenant studio.",
            )
        verify_tenant_active(admin.tenant)
        resolved_tenant_id = admin.tenant_id

    return {
        "user_id": admin.id,
        "tenant_id": resolved_tenant_id,
        "role": admin.role,
        "is_owner": admin.is_owner,
        "name": admin.name,
        "email": admin.email,
    }


def get_current_super_admin(
    current_admin: Annotated[dict[str, Any], Depends(get_current_admin)],
) -> dict[str, Any]:
    """
    Guards Super Admin management routes (/api/v1/admin/tenants/*) to strictly require role == 'super_admin'.
    """
    if current_admin.get("role") != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Platform Super Admin privileges required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_admin


# Centralized Modern FastAPI Dependency Aliases (Annotated)
CurrentAdmin = Annotated[dict[str, Any], Depends(get_current_admin)]
CurrentSuperAdmin = Annotated[dict[str, Any], Depends(get_current_super_admin)]
CurrentSubscriber = Annotated[dict[str, Any], Depends(get_current_subscriber)]
OptionalSubscriber = Annotated[dict[str, Any] | None, Depends(get_optional_subscriber)]
FormFile = Annotated[UploadFile, File(...)]
