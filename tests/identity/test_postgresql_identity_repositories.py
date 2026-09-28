from datetime import datetime, timezone
from types import SimpleNamespace
import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from industrial_oracle.core.exceptions import AuthenticationException
from industrial_oracle.core.security import hash_password
from industrial_oracle.identity.application.dtos import LoginRequest
from industrial_oracle.identity.application.services import AuthService
from industrial_oracle.identity.infrastructure.models import UserModel
from industrial_oracle.identity.infrastructure.repository import PostgreSQLUserRepository
from industrial_oracle.organization.infrastructure.models import MembershipModel
from industrial_oracle.organization.infrastructure.repository import PostgreSQLMembershipRepository


class FakeResult:
    def __init__(self, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def scalars(self):
        return SimpleNamespace(all=lambda: self._rows)

    def all(self):
        return self._rows

    def one_or_none(self):
        return self._rows[0] if self._rows else None


def user_model(
    *,
    email: str = "operator@example.test",
    password: str = "correct-horse-battery",
    active: bool = True,
) -> UserModel:
    now = datetime.now(timezone.utc)
    return UserModel(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        full_name="Test Operator",
        is_active=active,
        is_superuser=False,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_postgresql_user_repository_maps_user_and_normalizes_lookup_email() -> None:
    model = user_model()
    session = Mock()
    session.execute = AsyncMock(return_value=FakeResult(scalar=model))

    user = await PostgreSQLUserRepository(session).get_by_email("  OPERATOR@example.test ")

    assert user is not None
    assert user.id == model.id
    assert user.email == model.email
    assert user.password_hash == model.password_hash
    assert user.full_name == model.full_name
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at == model.created_at
    assert user.verify_password("correct-horse-battery")
    statement = session.execute.await_args.args[0]
    assert "lower(users.email)" in str(statement)
    assert "operator@example.test" in statement.compile().params.values()


@pytest.mark.asyncio
async def test_auth_service_uses_postgresql_repository_for_login_and_token() -> None:
    model = user_model()
    session = Mock()
    session.execute = AsyncMock(return_value=FakeResult(scalar=model))

    token = await AuthService(PostgreSQLUserRepository(session)).authenticate(
        LoginRequest(email=model.email, password="correct-horse-battery")
    )

    assert token.token_type == "bearer"
    assert token.access_token
    assert token.expires_in > 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model", "password"),
    [
        (None, "correct-horse-battery"),
        ("inactive", "correct-horse-battery"),
        ("active", "wrong-password"),
    ],
)
async def test_auth_service_rejects_unknown_inactive_and_wrong_password(model, password) -> None:
    result_model = None if model is None else user_model(active=model == "active")
    session = Mock()
    session.execute = AsyncMock(return_value=FakeResult(scalar=result_model))

    with pytest.raises(AuthenticationException):
        await AuthService(PostgreSQLUserRepository(session)).authenticate(
            LoginRequest(email="operator@example.test", password=password)
        )


@pytest.mark.asyncio
async def test_postgresql_user_repository_add_flushes_user_model() -> None:
    session = Mock()
    session.add = Mock()
    session.flush = AsyncMock()
    repository = PostgreSQLUserRepository(session)
    from industrial_oracle.identity.domain.models import User

    user = User(
        email="new-user@example.test",
        password_hash=hash_password("another-correct-password"),
        full_name="New User",
    )
    await repository.add(user)

    persisted = session.add.call_args.args[0]
    assert isinstance(persisted, UserModel)
    assert persisted.id == user.id
    assert persisted.email == user.email
    assert persisted.password_hash == user.password_hash
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_postgresql_user_list_is_scoped_to_organization_memberships() -> None:
    session = Mock()
    session.execute = AsyncMock(return_value=FakeResult(rows=[]))
    organization_id = uuid.uuid4()

    users = await PostgreSQLUserRepository(session).list_by_organization(organization_id)

    assert users == []
    statement = str(session.execute.await_args.args[0])
    assert "JOIN memberships" in statement
    assert "memberships.organization_id" in statement


@pytest.mark.asyncio
async def test_postgresql_membership_repository_maps_role_and_tenant_fields() -> None:
    organization_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    model = MembershipModel(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        role_id=uuid.uuid4(),
        status="ACTIVE",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    session = Mock()
    session.execute = AsyncMock(return_value=FakeResult(rows=[(model, "ENGINEER")]))

    membership = await PostgreSQLMembershipRepository(session).get_user_membership(
        user_id,
        organization_id,
    )

    assert membership is not None
    assert membership.user_id == user_id
    assert membership.organization_id == organization_id
    assert membership.role == "ENGINEER"
    assert membership.status == "ACTIVE"
    assert membership.is_active is True
    statement = str(session.execute.await_args.args[0])
    assert "memberships.user_id" in statement
    assert "memberships.organization_id" in statement


@pytest.mark.asyncio
async def test_postgresql_membership_list_is_scoped_to_organization() -> None:
    session = Mock()
    session.execute = AsyncMock(return_value=FakeResult(rows=[]))
    organization_id = uuid.uuid4()

    memberships = await PostgreSQLMembershipRepository(session).list_org_memberships(
        organization_id
    )

    assert memberships == []
    statement = str(session.execute.await_args.args[0])
    assert "memberships.organization_id" in statement
    assert organization_id in session.execute.await_args.args[0].compile().params.values()


@pytest.mark.asyncio
async def test_tenant_context_rejects_membership_with_non_active_status() -> None:
    from industrial_oracle.core.exceptions import AuthorizationException
    from industrial_oracle.core.security import get_tenant_context
    from industrial_oracle.identity.domain.models import User

    user_id = uuid.uuid4()
    organization_id = uuid.uuid4()
    membership_model = MembershipModel(
        id=uuid.uuid4(),
        user_id=user_id,
        organization_id=organization_id,
        role_id=uuid.uuid4(),
        status="INVITED",
        is_active=True,
    )
    session = Mock()
    session.execute = AsyncMock(
        return_value=FakeResult(rows=[(membership_model, "ADMIN")])
    )
    user = User(
        id=user_id,
        email="admin@example.test",
        password_hash=hash_password("some-development-password"),
        full_name="Admin",
    )

    with pytest.raises(AuthorizationException, match="no active organization memberships"):
        await get_tenant_context(current_user=user, session=session)


@pytest.mark.asyncio
async def test_postgresql_membership_repository_persists_role_and_active_state() -> None:
    from industrial_oracle.organization.domain.models import Membership

    session = Mock()
    session.execute = AsyncMock(return_value=FakeResult(scalar=uuid.uuid4()))
    session.add = Mock()
    session.flush = AsyncMock()
    membership = Membership(
        user_id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        role="VIEWER",
        status="INVITED",
        is_active=False,
    )

    await PostgreSQLMembershipRepository(session).add(membership)

    persisted = session.add.call_args.args[0]
    assert isinstance(persisted, MembershipModel)
    assert persisted.user_id == membership.user_id
    assert persisted.organization_id == membership.organization_id
    assert persisted.status == "INVITED"
    assert persisted.is_active is False
    session.flush.assert_awaited_once()
