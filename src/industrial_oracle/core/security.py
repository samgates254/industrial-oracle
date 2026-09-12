"""Security, cryptographic password hashing, JWT operations, and RBAC authorization dependencies."""

import base64
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from fastapi import Depends, Header, Request

from industrial_oracle.core.config import settings
from industrial_oracle.core.exceptions import (
    AuthenticationException,
    AuthorizationException,
    EntityNotFoundException,
    ValidationException,
)
from industrial_oracle.core.logging import actor_id_ctx, org_id_ctx


# ==============================================================================
# 1. Cryptographic Password Hashing (PBKDF2-HMAC-SHA256, 100,000 rounds)
# ==============================================================================

def hash_password(password: str) -> str:
    """Securely hashes a plaintext password with a random 16-byte salt using PBKDF2-SHA256."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"$pbkdf2-sha256${iterations}${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored PBKDF2-SHA256 hash using constant-time comparison."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 5 or parts[1] != "pbkdf2-sha256":
            return False
        iterations = int(parts[2])
        salt = parts[3]
        expected_hash = parts[4]
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(dk.hex(), expected_hash)
    except Exception:
        return False


# ==============================================================================
# 2. JWT Encoding and Decoding (RFC 7519 Compliant HMAC-SHA256)
# ==============================================================================

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates an RFC 7519 compliant HS256 JWT access token."""
    now = int(time.time())
    expire_seconds = (
        int(expires_delta.total_seconds())
        if expires_delta
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + expire_seconds,
    }
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}

    h_bytes = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    p_bytes = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{h_bytes}.{p_bytes}".encode("utf-8")

    signature = hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_str = _b64url_encode(signature)
    return f"{h_bytes}.{p_bytes}.{sig_str}"


def decode_access_token(token: str) -> Dict[str, Any]:
    """Validates signature and expiration of an access token, returning its claims."""
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthenticationException("Invalid authentication token format.")

    h_str, p_str, sig_str = parts
    signing_input = f"{h_str}.{p_str}".encode("utf-8")
    expected_sig = hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    try:
        actual_sig = _b64url_decode(sig_str)
    except Exception:
        raise AuthenticationException("Invalid token signature encoding.")

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise AuthenticationException("Invalid token signature.")

    try:
        payload_bytes = _b64url_decode(p_str)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise AuthenticationException("Corrupted token payload.")

    now = int(time.time())
    if "exp" in payload and payload["exp"] < now:
        raise AuthenticationException("Authentication token has expired. Please log in again.")

    return payload


# ==============================================================================
# 3. Roles and Explicit Permissions Registry
# ==============================================================================

class RoleEnum:
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    ENGINEER = "ENGINEER"
    OPERATOR = "OPERATOR"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

    ALL_ROLES = [OWNER, ADMIN, ENGINEER, OPERATOR, ANALYST, VIEWER]


class PermissionEnum:
    ORGANIZATION_READ = "organization.read"
    ORGANIZATION_UPDATE = "organization.update"

    USERS_READ = "users.read"
    USERS_CREATE = "users.create"
    USERS_UPDATE = "users.update"
    USERS_DISABLE = "users.disable"

    ASSETS_READ = "assets.read"
    ASSETS_CREATE = "assets.create"
    ASSETS_UPDATE = "assets.update"
    ASSETS_DELETE = "assets.delete"

    OPERATIONS_READ = "operations.read"
    OPERATIONS_CREATE = "operations.create"
    OPERATIONS_UPDATE = "operations.update"

    MAINTENANCE_READ = "maintenance.read"
    MAINTENANCE_CREATE = "maintenance.create"
    MAINTENANCE_UPDATE = "maintenance.update"

    INVENTORY_READ = "inventory.read"
    INVENTORY_CREATE = "inventory.create"
    INVENTORY_UPDATE = "inventory.update"

    OPTIMIZATION_READ = "optimization.read"
    OPTIMIZATION_RUN = "optimization.run"

    AUDIT_READ = "audit.read"

    INTEGRATION_READ = "integration.read"
    INTEGRATION_MANAGE = "integration.manage"
    INTEGRATION_RETRY = "integration.retry"


ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    RoleEnum.OWNER: {
        PermissionEnum.ORGANIZATION_READ,
        PermissionEnum.ORGANIZATION_UPDATE,
        PermissionEnum.USERS_READ,
        PermissionEnum.USERS_CREATE,
        PermissionEnum.USERS_UPDATE,
        PermissionEnum.USERS_DISABLE,
        PermissionEnum.ASSETS_READ,
        PermissionEnum.ASSETS_CREATE,
        PermissionEnum.ASSETS_UPDATE,
        PermissionEnum.ASSETS_DELETE,
        PermissionEnum.OPERATIONS_READ,
        PermissionEnum.OPERATIONS_CREATE,
        PermissionEnum.OPERATIONS_UPDATE,
        PermissionEnum.MAINTENANCE_READ,
        PermissionEnum.MAINTENANCE_CREATE,
        PermissionEnum.MAINTENANCE_UPDATE,
        PermissionEnum.INVENTORY_READ,
        PermissionEnum.INVENTORY_CREATE,
        PermissionEnum.INVENTORY_UPDATE,
        PermissionEnum.OPTIMIZATION_READ,
        PermissionEnum.OPTIMIZATION_RUN,
        PermissionEnum.AUDIT_READ,
        PermissionEnum.INTEGRATION_READ,
        PermissionEnum.INTEGRATION_MANAGE,
        PermissionEnum.INTEGRATION_RETRY,
    },
    RoleEnum.ADMIN: {
        PermissionEnum.ORGANIZATION_READ,
        PermissionEnum.ORGANIZATION_UPDATE,
        PermissionEnum.USERS_READ,
        PermissionEnum.USERS_CREATE,
        PermissionEnum.USERS_UPDATE,
        PermissionEnum.USERS_DISABLE,
        PermissionEnum.ASSETS_READ,
        PermissionEnum.ASSETS_CREATE,
        PermissionEnum.ASSETS_UPDATE,
        PermissionEnum.ASSETS_DELETE,
        PermissionEnum.OPERATIONS_READ,
        PermissionEnum.OPERATIONS_CREATE,
        PermissionEnum.OPERATIONS_UPDATE,
        PermissionEnum.MAINTENANCE_READ,
        PermissionEnum.MAINTENANCE_CREATE,
        PermissionEnum.MAINTENANCE_UPDATE,
        PermissionEnum.INVENTORY_READ,
        PermissionEnum.INVENTORY_CREATE,
        PermissionEnum.INVENTORY_UPDATE,
        PermissionEnum.OPTIMIZATION_READ,
        PermissionEnum.OPTIMIZATION_RUN,
        PermissionEnum.AUDIT_READ,
        PermissionEnum.INTEGRATION_READ,
        PermissionEnum.INTEGRATION_MANAGE,
        PermissionEnum.INTEGRATION_RETRY,
    },
    RoleEnum.ENGINEER: {
        PermissionEnum.ORGANIZATION_READ,
        PermissionEnum.USERS_READ,
        PermissionEnum.ASSETS_READ,
        PermissionEnum.ASSETS_CREATE,
        PermissionEnum.ASSETS_UPDATE,
        PermissionEnum.ASSETS_DELETE,
        PermissionEnum.OPERATIONS_READ,
        PermissionEnum.OPERATIONS_CREATE,
        PermissionEnum.OPERATIONS_UPDATE,
        PermissionEnum.MAINTENANCE_READ,
        PermissionEnum.MAINTENANCE_CREATE,
        PermissionEnum.MAINTENANCE_UPDATE,
        PermissionEnum.INVENTORY_READ,
        PermissionEnum.INVENTORY_CREATE,
        PermissionEnum.INVENTORY_UPDATE,
        PermissionEnum.OPTIMIZATION_READ,
        PermissionEnum.OPTIMIZATION_RUN,
        PermissionEnum.AUDIT_READ,
        PermissionEnum.INTEGRATION_READ,
        PermissionEnum.INTEGRATION_MANAGE,
    },
    RoleEnum.OPERATOR: {
        PermissionEnum.ORGANIZATION_READ,
        PermissionEnum.ASSETS_READ,
        PermissionEnum.OPERATIONS_READ,
        PermissionEnum.OPERATIONS_CREATE,
        PermissionEnum.OPERATIONS_UPDATE,
        PermissionEnum.MAINTENANCE_READ,
        PermissionEnum.MAINTENANCE_CREATE,
        PermissionEnum.MAINTENANCE_UPDATE,
        PermissionEnum.INVENTORY_READ,
        PermissionEnum.INVENTORY_UPDATE,
    },
    RoleEnum.ANALYST: {
        PermissionEnum.ORGANIZATION_READ,
        PermissionEnum.ASSETS_READ,
        PermissionEnum.OPERATIONS_READ,
        PermissionEnum.MAINTENANCE_READ,
        PermissionEnum.INVENTORY_READ,
        PermissionEnum.OPTIMIZATION_READ,
        PermissionEnum.OPTIMIZATION_RUN,
        PermissionEnum.AUDIT_READ,
        PermissionEnum.INTEGRATION_READ,
    },
    RoleEnum.VIEWER: {
        PermissionEnum.ORGANIZATION_READ,
        PermissionEnum.ASSETS_READ,
        PermissionEnum.OPERATIONS_READ,
        PermissionEnum.MAINTENANCE_READ,
        PermissionEnum.INVENTORY_READ,
        PermissionEnum.OPTIMIZATION_READ,
        PermissionEnum.INTEGRATION_READ,
    },
}


# ==============================================================================
# 4. Tenant Context & Request Dependencies
# ==============================================================================

class TenantContext:
    """Resolved tenant context associated with the authenticated request."""

    def __init__(
        self,
        user: Any,
        organization: Any,
        membership: Any,
        role: str,
        permissions: Set[str],
    ) -> None:
        self.user = user
        self.organization = organization
        self.membership = membership
        self.role = role
        self.permissions = permissions

    @property
    def organization_id(self) -> uuid.UUID:
        return self.organization.id

    @property
    def org_id(self) -> str:
        return str(self.organization.id)

    @property
    def user_id(self) -> uuid.UUID:
        return self.user.id

    def require_permission(self, permission: Any) -> None:
        perm_val = permission.value if hasattr(permission, "value") else str(permission)
        if perm_val not in self.permissions:
            raise AuthorizationException(f"Permission denied: missing '{perm_val}'")


def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    """Extracts the Bearer token from the HTTP Authorization header."""
    if not authorization:
        raise AuthenticationException("Authorization header missing.")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationException("Invalid authorization scheme. Use 'Bearer <token>'.")

    return parts[1]


async def get_current_user(token: str = Depends(get_token_from_header)) -> Any:
    """Resolves and validates the authenticated user from the JWT token."""
    from industrial_oracle.identity.infrastructure.repository import user_repo

    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationException("Invalid token: subject missing.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationException("Invalid token subject format.")

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise AuthenticationException("User account not found.")

    if not user.is_active:
        raise AuthenticationException("User account is inactive. Please contact your administrator.")

    actor_id_ctx.set(str(user.id))
    return user


async def get_tenant_context(
    current_user: Any = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> TenantContext:
    """Derives and validates organization isolation context for the request.

    Enforces:
    1. The client-provided X-Organization-ID is never trusted implicitly.
    2. Server verifies the user has an active membership in the target organization.
    3. Populates permissions derived from the user's role in that organization.
    """
    from industrial_oracle.organization.infrastructure.repository import (
        membership_repo,
        organization_repo,
    )

    user_memberships = await membership_repo.list_user_memberships(current_user.id)
    active_memberships = [m for m in user_memberships if m.is_active]

    if not active_memberships:
        raise AuthorizationException("User has no active organization memberships.")

    target_org_id: Optional[uuid.UUID] = None

    if x_organization_id:
        try:
            target_org_id = uuid.UUID(x_organization_id)
        except ValueError:
            raise ValidationException("Invalid X-Organization-ID header format. Must be a valid UUID.")
        
        # Verify the user actually belongs to this requested organization
        matching_membership = next(
            (m for m in active_memberships if m.organization_id == target_org_id),
            None,
        )
        if not matching_membership:
            raise AuthorizationException(
                "Access denied. User is not an active member of the specified organization.",
            )
        chosen_membership = matching_membership
    else:
        if len(active_memberships) == 1:
            chosen_membership = active_memberships[0]
            target_org_id = chosen_membership.organization_id
        else:
            raise ValidationException(
                "User belongs to multiple organizations. Please specify the target organization using the 'X-Organization-ID' header.",
            )

    org = await organization_repo.get_by_id(target_org_id)
    if not org or org.status != "ACTIVE":
        raise AuthorizationException("Organization is not active or does not exist.")

    role = chosen_membership.role
    permissions = ROLE_PERMISSIONS.get(role, set())

    # Set organization context for tracing
    org_id_ctx.set(str(org.id))

    return TenantContext(
        user=current_user,
        organization=org,
        membership=chosen_membership,
        role=role,
        permissions=permissions,
    )


def require_role(*allowed_roles: str) -> Callable[[TenantContext], TenantContext]:
    """Dependency factory checking that the user's role in the organization is permitted."""
    async def role_checker(ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if ctx.role not in allowed_roles:
            raise AuthorizationException(
                f"Action requires one of roles: {', '.join(allowed_roles)}. Your role is: {ctx.role}.",
                required_role=",".join(allowed_roles),
            )
        return ctx
    return role_checker


def require_permission(*required_perms: str) -> Callable[[TenantContext], TenantContext]:
    """Dependency factory checking that the user has all required permissions."""
    async def perm_checker(ctx: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        missing = [p for p in required_perms if p not in ctx.permissions]
        if missing:
            raise AuthorizationException(
                f"Action requires permissions: {', '.join(required_perms)}. Missing: {', '.join(missing)}.",
                details={"missing_permissions": missing},
            )
        return ctx
    return perm_checker


# ==============================================================================
# 5. Symmetric Secret Encryption at Rest (AES-128-CBC / Fernet)
# ==============================================================================

def get_secret_cipher() -> Any:
    """Instantiates Fernet cipher derived from settings secret."""
    from cryptography.fernet import Fernet
    key_src = getattr(settings, "WEBHOOK_ENCRYPTION_KEY", None) or settings.JWT_SECRET
    derived_key = base64.urlsafe_b64encode(hashlib.sha256(key_src.encode("utf-8")).digest())
    return Fernet(derived_key)


def encrypt_secret(plain_text: str) -> str:
    """Encrypts sensitive plaintext strings (e.g. webhook secrets) for storage at rest."""
    if not plain_text:
        return ""
    try:
        cipher = get_secret_cipher()
        return cipher.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return plain_text


def decrypt_secret(cipher_text: str) -> str:
    """Decrypts ciphertext back to plaintext. Falls back to original string if not encrypted."""
    if not cipher_text:
        return ""
    try:
        cipher = get_secret_cipher()
        return cipher.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return cipher_text
