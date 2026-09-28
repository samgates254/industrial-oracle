from collections import defaultdict
import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from apps.cli.create_dev_admin import bootstrap_development_admin
from industrial_oracle.core.config import settings
from industrial_oracle.core.security import ROLE_PERMISSIONS, RoleEnum, verify_password
from industrial_oracle.identity.infrastructure.models import (
    PermissionModel,
    RoleModel,
    RolePermissionModel,
    UserModel,
)
from industrial_oracle.organization.infrastructure.models import (
    MembershipModel,
    OrganizationModel,
)


class FakeResult:
    def __init__(self, scalar=None, row=None):
        self._scalar = scalar
        self._row = row

    def scalar_one_or_none(self):
        return self._scalar

    def one_or_none(self):
        return self._row


class BootstrapSession:
    def __init__(self):
        self.rows = defaultdict(list)
        self.pending = []

    async def execute(self, statement):
        model = statement.column_descriptions[0]["entity"]
        values = statement.compile().params
        if model is RoleModel:
            value = next(iter(values.values()))
            return FakeResult(next((row for row in self.rows[RoleModel] if row.name == value), None))
        if model is PermissionModel:
            value = next(iter(values.values()))
            return FakeResult(
                next((row for row in self.rows[PermissionModel] if row.code == value), None)
            )
        if model is OrganizationModel:
            value = next(iter(values.values()))
            return FakeResult(
                next((row for row in self.rows[OrganizationModel] if row.slug.lower() == value), None)
            )
        if model is UserModel:
            value = next(iter(values.values()))
            return FakeResult(
                next((row for row in self.rows[UserModel] if row.email.lower() == value), None)
            )
        if model is MembershipModel:
            user_id = values["user_id_1"]
            organization_id = values["organization_id_1"]
            membership = next(
                (
                    row
                    for row in self.rows[MembershipModel]
                    if row.user_id == user_id and row.organization_id == organization_id
                ),
                None,
            )
            if membership is None:
                return FakeResult()
            role = next(row for row in self.rows[RoleModel] if row.id == membership.role_id)
            return FakeResult(row=(membership, role.name))
        raise AssertionError(f"Unexpected query model: {model}")

    async def get(self, model, key):
        if model is RolePermissionModel:
            return next(
                (
                    row
                    for row in self.rows[RolePermissionModel]
                    if (row.role_id, row.permission_id) == key
                ),
                None,
            )
        raise AssertionError(f"Unexpected get model: {model}")

    def add(self, instance):
        self.pending.append(instance)

    async def flush(self):
        while self.pending:
            instance = self.pending.pop(0)
            if hasattr(instance, "id") and instance.id is None:
                instance.id = uuid.uuid4()
            self.rows[type(instance)].append(instance)


@pytest.mark.asyncio
async def test_development_bootstrap_creates_admin_and_is_idempotent(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    session = BootstrapSession()

    first = await bootstrap_development_admin(
        session,
        email="  Dev.Admin@example.test ",
        password="a-unique-development-password",
        full_name="Development Admin",
    )
    saved_user = session.rows[UserModel][0]
    saved_password_hash = saved_user.password_hash

    second = await bootstrap_development_admin(
        session,
        email="dev.admin@example.test",
        password="a-different-password-is-ignored",
        full_name="Changed Name Is Ignored",
    )

    assert first.created_user is True
    assert first.created_organization is True
    assert first.created_membership is True
    assert second.created_user is False
    assert second.created_organization is False
    assert second.created_membership is False
    assert len(session.rows[UserModel]) == 1
    assert len(session.rows[OrganizationModel]) == 1
    assert len(session.rows[MembershipModel]) == 1
    assert saved_user.password_hash == saved_password_hash
    assert saved_user.password_hash != "a-unique-development-password"
    assert verify_password("a-unique-development-password", saved_user.password_hash)
    assert saved_user.email == "dev.admin@example.test"
    assert saved_user.is_superuser is False
    membership = session.rows[MembershipModel][0]
    role = next(row for row in session.rows[RoleModel] if row.id == membership.role_id)
    assert role.name == RoleEnum.ADMIN
    granted_codes = {
        permission.code
        for permission in session.rows[PermissionModel]
        if any(
            link.role_id == role.id and link.permission_id == permission.id
            for link in session.rows[RolePermissionModel]
        )
    }
    assert granted_codes == ROLE_PERMISSIONS[RoleEnum.ADMIN]


@pytest.mark.asyncio
async def test_development_bootstrap_is_disabled_outside_development(monkeypatch) -> None:
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    session = Mock()
    session.execute = AsyncMock()

    with pytest.raises(RuntimeError, match="disabled outside development"):
        await bootstrap_development_admin(
            session,
            email="dev.admin@example.test",
            password="a-unique-development-password",
            full_name="Development Admin",
        )

    session.execute.assert_not_awaited()


def test_role_permission_model_matches_existing_join_table_schema() -> None:
    assert set(RolePermissionModel.__table__.columns.keys()) == {
        "role_id",
        "permission_id",
    }
