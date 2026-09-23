import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status

from app.config import get_settings


def create_access_token(
    user_id: int,
    role: str = "subscriber",
    username: str = "",
    tenant_id: int | None = None,
    expires_delta_minutes: int | None = None,
) -> str:
    """
    Encodes user_id, role, username, and tenant_id into a signed JWT access token.
    Roles: 'super_admin' (Platform Super Admin), 'admin' (Tenant Creator Studio),
    'subscriber' (Mobile App), or 'guest' (Mobile App Guest).
    """
    settings = get_settings()
    if expires_delta_minutes is None:
        expires_delta_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    secret_key = settings.JWT_SECRET_KEY
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta_minutes)

    to_encode = {
        "sub": str(user_id),
        "user_id": user_id,
        "role": role,
        "username": username,
        "tenant_id": tenant_id,
        "exp": expire,
    }
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token_string() -> str:
    """
    Generates a cryptographically secure 64-character hex random string for refresh token.
    """
    return secrets.token_hex(32)


def hash_refresh_token(token: str) -> str:
    """
    Computes SHA-256 hash string of raw refresh token for safe DB storage.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> dict:
    """
    Decodes JWT Bearer token and returns claims payload dictionary.
    Raises HTTPException(401) if token is expired or invalid.
    """
    settings = get_settings()
    secret_key = settings.JWT_SECRET_KEY

    try:
        payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def hash_password(password: str, iterations: int = 600000) -> str:
    """
    Hashes a plaintext password using PBKDF2-HMAC-SHA256 with a 16-byte random salt and 600,000 iterations.
    Format: pbkdf2_sha256$600000$<salt_hex>$<hash_hex>
    """
    salt = secrets.token_bytes(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${hash_bytes.hex()}"


def verify_password(plain_password: str, password_hash: str | None) -> bool:
    """
    Verifies a plaintext password against a stored PBKDF2-HMAC-SHA256 hash using secrets.compare_digest.
    """
    if not password_hash:
        return False

    parts = password_hash.split("$")
    if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
        return False

    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = parts[3]
    except (ValueError, IndexError):
        return False

    computed_hash = hashlib.pbkdf2_hmac(
        "sha256", plain_password.encode("utf-8"), salt, iterations
    ).hex()

    return secrets.compare_digest(computed_hash, expected_hash)


def is_tenant_active(tenant_or_id: object) -> bool:
    """
    Checks if a tenant studio exists and is currently active.
    Returns boolean True/False without raising an exception.
    Accepts either an integer tenant_id or an existing Tenant Peewee model instance.
    """
    from app.models.tenant import Tenant

    if isinstance(tenant_or_id, Tenant):
        return bool(getattr(tenant_or_id, "is_active", True))
    if not tenant_or_id:
        return False
    tenant = Tenant.get_or_none(Tenant.id == tenant_or_id)
    return bool(tenant and getattr(tenant, "is_active", True))


def verify_tenant_active(tenant_or_id: object) -> object:
    """
    Verifies that a tenant studio exists and is currently active.
    Raises HTTPException(403) if deactivated, suspended, or not found.
    Accepts either an integer tenant_id or an existing Tenant Peewee model instance.
    """
    from app.models.tenant import Tenant

    if isinstance(tenant_or_id, Tenant):
        tenant = tenant_or_id
    elif tenant_or_id:
        tenant = Tenant.get_or_none(Tenant.id == tenant_or_id)
    else:
        tenant = None

    if not tenant or not getattr(tenant, "is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Studio tenant is currently deactivated or suspended.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return tenant

