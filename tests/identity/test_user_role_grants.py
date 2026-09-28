import uuid

import pytest

from industrial_oracle.core.exceptions import AuthorizationException, ValidationException
from industrial_oracle.core.security import RoleEnum
from industrial_oracle.identity.application.dtos import UserCreateDTO
from industrial_oracle.identity.application.services import UserService
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import InMemoryUserRepository
from industrial_oracle.organization.domain.models import Membership, Organization
from industrial_oracle.organization.infrastructure.repository import (
    InMemoryMembershipRepository,
    InMemoryOrganizationRepository,
)


@pytest.fixture
def user_service_context():
    users = InMemoryUserRepository()
    memberships = InMemoryMembershipRepository()
    organizations = InMemoryOrganizationRepository()
    organization = Organization(name="Test Organization", slug=f"test-{uuid.uuid4()}")

    async def prepare():
        await organizations.add(organization)

    async def add_actor(role: str) -> User:
        actor = User(
            email=f"{role.lower()}-{uuid.uuid4()}@example.test",
            password_hash="unused",
            full_name=f"{role} Actor",
        )
        await users.add(actor)
        await memberships.add(Membership(actor.id, organization.id, role))
        return actor

    service = UserService(users, memberships, organizations)
    return service, users, memberships, organization, prepare, add_actor


def create_dto(role: str, email: str | None = None) -> UserCreateDTO:
    return UserCreateDTO(
        email=email or f"new-{uuid.uuid4()}@example.test",
        password="valid-test-password",
        full_name="New User",
        role=role,
    )


@pytest.mark.asyncio
async def test_admin_cannot_grant_owner(user_service_context) -> None:
    service, _, _, organization, prepare, add_actor = user_service_context
    await prepare()
    admin = await add_actor(RoleEnum.ADMIN)

    with pytest.raises(AuthorizationException):
        await service.create_user_in_org(create_dto(RoleEnum.OWNER), organization.id, admin.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "role",
    [RoleEnum.ADMIN, RoleEnum.ENGINEER, RoleEnum.OPERATOR, RoleEnum.ANALYST, RoleEnum.VIEWER],
)
async def test_admin_can_grant_permitted_roles(user_service_context, role: str) -> None:
    service, _, memberships, organization, prepare, add_actor = user_service_context
    await prepare()
    admin = await add_actor(RoleEnum.ADMIN)

    created = await service.create_user_in_org(create_dto(role), organization.id, admin.id)

    membership = await memberships.get_user_membership(created.id, organization.id)
    assert membership is not None
    assert membership.role == role


@pytest.mark.asyncio
@pytest.mark.parametrize("role", RoleEnum.ALL_ROLES)
async def test_owner_can_grant_each_defined_role(user_service_context, role: str) -> None:
    service, _, memberships, organization, prepare, add_actor = user_service_context
    await prepare()
    owner = await add_actor(RoleEnum.OWNER)

    created = await service.create_user_in_org(create_dto(role), organization.id, owner.id)

    membership = await memberships.get_user_membership(created.id, organization.id)
    assert membership is not None
    assert membership.role == role


@pytest.mark.asyncio
async def test_invalid_role_is_rejected(user_service_context) -> None:
    service, _, _, organization, prepare, add_actor = user_service_context
    await prepare()
    owner = await add_actor(RoleEnum.OWNER)

    with pytest.raises(ValidationException):
        await service.create_user_in_org(create_dto("SUPERUSER"), organization.id, owner.id)


@pytest.mark.asyncio
async def test_invalid_role_is_rejected_for_existing_user(user_service_context) -> None:
    service, users, _, organization, prepare, add_actor = user_service_context
    await prepare()
    owner = await add_actor(RoleEnum.OWNER)
    existing = User(
        email="existing-invalid-role@example.test",
        password_hash="unused",
        full_name="Existing User",
    )
    await users.add(existing)

    with pytest.raises(ValidationException):
        await service.create_user_in_org(
            create_dto("SUPERUSER", existing.email),
            organization.id,
            owner.id,
        )


@pytest.mark.asyncio
async def test_existing_user_membership_uses_same_role_grant_policy(user_service_context) -> None:
    service, users, memberships, organization, prepare, add_actor = user_service_context
    await prepare()
    admin = await add_actor(RoleEnum.ADMIN)
    existing = User(
        email="existing@example.test",
        password_hash="unused",
        full_name="Existing User",
    )
    await users.add(existing)

    with pytest.raises(AuthorizationException):
        await service.create_user_in_org(
            create_dto(RoleEnum.OWNER, existing.email),
            organization.id,
            admin.id,
        )

    assert await memberships.get_user_membership(existing.id, organization.id) is None


@pytest.mark.asyncio
async def test_admin_can_assign_permitted_role_to_existing_user(user_service_context) -> None:
    service, users, memberships, organization, prepare, add_actor = user_service_context
    await prepare()
    admin = await add_actor(RoleEnum.ADMIN)
    existing = User(
        email="existing-permitted@example.test",
        password_hash="unused",
        full_name="Existing User",
    )
    await users.add(existing)

    await service.create_user_in_org(
        create_dto(RoleEnum.ENGINEER, existing.email),
        organization.id,
        admin.id,
    )

    membership = await memberships.get_user_membership(existing.id, organization.id)
    assert membership is not None
    assert membership.role == RoleEnum.ENGINEER
