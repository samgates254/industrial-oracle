"""Authentication and User Management API endpoints."""

from typing import List
import uuid
from fastapi import APIRouter, Depends

from industrial_oracle.core.security import (
    PermissionEnum,
    TenantContext,
    get_current_user,
    get_tenant_context,
    require_permission,
)
from industrial_oracle.identity.application.dtos import (
    LoginRequest,
    TokenResponse,
    UserCreateDTO,
    UserProfileResponseDTO,
    UserResponseDTO,
    UserStatusUpdateDTO,
    UserUpdateDTO,
)
from industrial_oracle.identity.application.services import AuthService, UserService
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
)

router = APIRouter(prefix="/api/v1", tags=["Identity & Users"])

auth_service = AuthService(user_repo)
user_service = UserService(user_repo, membership_repo, organization_repo)


# ==============================================================================
# Authentication Endpoints
# ==============================================================================

@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticates user credentials and issues an RFC 7519 JWT access token."""
    return await auth_service.authenticate(request)


# ==============================================================================
# User Management Endpoints
# ==============================================================================

@router.get("/users/me", response_model=UserProfileResponseDTO)
async def get_my_profile(current_user=Depends(get_current_user)):
    """Retrieves authenticated user profile along with active organization memberships."""
    return await user_service.get_profile(current_user.id)


@router.get(
    "/users",
    response_model=List[UserResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.USERS_READ))],
)
async def list_users(ctx: TenantContext = Depends(get_tenant_context)):
    """Lists users belonging to the caller's authenticated organization."""
    return await user_service.list_organization_users(ctx.organization.id)


@router.post(
    "/users",
    response_model=UserResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.USERS_CREATE))],
)
async def create_user(
    dto: UserCreateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Creates a user and provisions membership in the caller's organization."""
    return await user_service.create_user_in_org(dto, ctx.organization.id, ctx.user.id)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.USERS_UPDATE))],
)
async def update_user(
    user_id: uuid.UUID,
    dto: UserUpdateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Updates user details for a member of the caller's organization."""
    return await user_service.update_user(user_id, dto, ctx.organization.id, ctx.user.id)


@router.patch(
    "/users/{user_id}/status",
    response_model=UserResponseDTO,
    dependencies=[Depends(require_permission(PermissionEnum.USERS_DISABLE))],
)
async def update_user_status(
    user_id: uuid.UUID,
    dto: UserStatusUpdateDTO,
    ctx: TenantContext = Depends(get_tenant_context),
):
    """Activates or deactivates a user account within the caller's organization."""
    return await user_service.update_user_status(user_id, dto.is_active, ctx.organization.id, ctx.user.id)
