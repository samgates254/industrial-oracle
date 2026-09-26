"""Identity and User application services with audit integration."""

from datetime import timedelta
from typing import List, Optional
import uuid

from industrial_oracle.audit.application.service import audit_service
from industrial_oracle.core.config import settings
from industrial_oracle.core.exceptions import (
    AuthenticationException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
    ValidationException,
)
from industrial_oracle.core.security import (
    RoleEnum,
    create_access_token,
    hash_password,
)
from industrial_oracle.identity.application.dtos import (
    LoginRequest,
    TokenResponse,
    UserCreateDTO,
    UserProfileResponseDTO,
    UserResponseDTO,
    UserUpdateDTO,
)
from industrial_oracle.identity.application.interfaces import IUserRepository
from industrial_oracle.identity.domain.models import User
from industrial_oracle.organization.application.dtos import MembershipResponseDTO
from industrial_oracle.organization.application.interfaces import (
    IMembershipRepository,
    IOrganizationRepository,
)
from industrial_oracle.organization.domain.models import Membership


class AuthService:
    """Manages user authentication and token creation."""

    def __init__(self, user_repo: IUserRepository) -> None:
        self.user_repo = user_repo

    async def authenticate(self, request: LoginRequest) -> TokenResponse:
        """Authenticates credentials, rejecting invalid combinations without leaking state."""
        clean_email = request.email.strip().lower()
        user = await self.user_repo.get_by_email(clean_email)

        # Do not leak whether user exists or password is wrong
        if not user or not user.verify_password(request.password):
            raise AuthenticationException("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationException("User account is inactive. Please contact your administrator.")

        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(user.id, user.email, expires_delta=expires_delta)

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )


class UserService:
    """Manages user accounts, membership provisioning, and lifecycle state."""

    def __init__(
        self,
        user_repo: IUserRepository,
        membership_repo: IMembershipRepository,
        org_repo: IOrganizationRepository,
    ) -> None:
        self.user_repo = user_repo
        self.membership_repo = membership_repo
        self.org_repo = org_repo

    async def get_profile(self, user_id: uuid.UUID) -> UserProfileResponseDTO:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)

        memberships = await self.membership_repo.list_user_memberships(user.id)
        membership_dtos = []
        for m in memberships:
            org = await self.org_repo.get_by_id(m.organization_id)
            org_name = org.name if org else "Unknown"
            membership_dtos.append(
                MembershipResponseDTO(
                    id=m.id,
                    organization_id=m.organization_id,
                    organization_name=org_name,
                    role=m.role,
                    is_active=m.is_active,
                    created_at=m.created_at,
                )
            )

        return UserProfileResponseDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            memberships=membership_dtos,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def list_organization_users(self, organization_id: uuid.UUID) -> List[UserResponseDTO]:
        users = await self.user_repo.list_by_organization(organization_id)
        return [
            UserResponseDTO(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                is_active=u.is_active,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in users
        ]

    async def create_user_in_org(
        self,
        dto: UserCreateDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> UserResponseDTO:
        clean_email = dto.email.strip().lower()
        existing = await self.user_repo.get_by_email(clean_email)

        if existing:
            existing_membership = await self.membership_repo.get_user_membership(existing.id, organization_id)
            if existing_membership:
                raise EntityAlreadyExistsException("Membership", "email", clean_email)
            user = existing
        else:
            if dto.role not in RoleEnum.ALL_ROLES:
                raise ValidationException(f"Invalid role: {dto.role}. Allowed: {RoleEnum.ALL_ROLES}")
            
            pwd_hash = hash_password(dto.password)
            user = User(
                email=clean_email,
                password_hash=pwd_hash,
                full_name=dto.full_name,
            )
            await self.user_repo.add(user)

        membership = Membership(
            user_id=user.id,
            organization_id=organization_id,
            role=dto.role,
        )
        await self.membership_repo.add(membership)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="USER_CREATED",
            resource_type="User",
            resource_id=str(user.id),
            new_value={"email": user.email, "role": dto.role},
        )

        return UserResponseDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def update_user(
        self,
        user_id: uuid.UUID,
        dto: UserUpdateDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> UserResponseDTO:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)

        membership = await self.membership_repo.get_user_membership(user.id, organization_id)
        if not membership:
            raise EntityNotFoundException("User", user_id)

        old_state = {"email": user.email, "full_name": user.full_name}
        user.update_profile(full_name=dto.full_name, email=dto.email)
        await self.user_repo.update(user)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="USER_UPDATED",
            resource_type="User",
            resource_id=str(user.id),
            old_value=old_state,
            new_value={"email": user.email, "full_name": user.full_name},
        )

        return UserResponseDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    async def update_user_status(
        self,
        user_id: uuid.UUID,
        is_active: bool,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> UserResponseDTO:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)

        membership = await self.membership_repo.get_user_membership(user.id, organization_id)
        if not membership:
            raise EntityNotFoundException("User", user_id)

        old_status = user.is_active
        if is_active:
            user.activate()
        else:
            user.deactivate()

        await self.user_repo.update(user)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="USER_STATUS_CHANGED",
            resource_type="User",
            resource_id=str(user.id),
            old_value={"is_active": old_status},
            new_value={"is_active": is_active},
        )

        return UserResponseDTO(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
