"""Create a development-only administrator and its organization membership."""

import asyncio
from dataclasses import dataclass
from getpass import getpass
import os
import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from industrial_oracle.core.config import settings
from industrial_oracle.core.database import db_manager
from industrial_oracle.core.security import ROLE_PERMISSIONS, RoleEnum, hash_password
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


@dataclass(frozen=True)
class BootstrapResult:
    user_id: str
    organization_id: str
    created_user: bool
    created_organization: bool
    created_membership: bool


async def bootstrap_development_admin(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    full_name: str,
    organization_name: str = "Development Organization",
    organization_slug: str = "development",
) -> BootstrapResult:
    """Idempotently create a new development admin without changing existing accounts."""
    if settings.ENVIRONMENT.casefold() != "development":
        raise RuntimeError("Development administrator bootstrap is disabled outside development.")

    clean_email = email.strip().lower()
    clean_name = full_name.strip()
    clean_org_name = organization_name.strip()
    clean_org_slug = organization_slug.strip().lower()
    if not clean_email or "@" not in clean_email or any(c.isspace() for c in clean_email):
        raise ValueError("A valid development administrator email is required.")
    if len(password) < 8:
        raise ValueError("Development administrator password must be at least 8 characters.")
    if len(clean_name) < 2:
        raise ValueError("Development administrator name must be at least 2 characters.")
    slug_is_valid = re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", clean_org_slug)
    if not clean_org_name or not slug_is_valid:
        raise ValueError("Organization name and a lowercase hyphenated slug are required.")

    role_result = await session.execute(
        select(RoleModel).where(RoleModel.name == RoleEnum.ADMIN)
    )
    role = role_result.scalar_one_or_none()
    if role is None:
        role = RoleModel(name=RoleEnum.ADMIN, description="Organization administrator")
        session.add(role)
        await session.flush()

    for permission_code in sorted(ROLE_PERMISSIONS[RoleEnum.ADMIN]):
        permission_result = await session.execute(
            select(PermissionModel).where(PermissionModel.code == permission_code)
        )
        permission = permission_result.scalar_one_or_none()
        if permission is None:
            permission = PermissionModel(code=permission_code)
            session.add(permission)
            await session.flush()

        role_permission = await session.get(
            RolePermissionModel,
            (role.id, permission.id),
        )
        if role_permission is None:
            session.add(
                RolePermissionModel(role_id=role.id, permission_id=permission.id)
            )

    organization_result = await session.execute(
        select(OrganizationModel).where(
            func.lower(OrganizationModel.slug) == clean_org_slug
        )
    )
    organization = organization_result.scalar_one_or_none()
    created_organization = organization is None
    if organization is None:
        organization = OrganizationModel(
            name=clean_org_name,
            slug=clean_org_slug,
            status="ACTIVE",
        )
        session.add(organization)
        await session.flush()
    elif organization.status != "ACTIVE":
        raise ValueError("The requested development organization is not active.")

    user_result = await session.execute(
        select(UserModel).where(func.lower(UserModel.email) == clean_email)
    )
    user = user_result.scalar_one_or_none()
    created_user = user is None
    if user is None:
        user = UserModel(
            email=clean_email,
            password_hash=hash_password(password),
            full_name=clean_name,
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        await session.flush()
    elif not user.is_active:
        raise ValueError("The existing development administrator account is inactive.")

    membership_result = await session.execute(
        select(MembershipModel, RoleModel.name)
        .join(RoleModel, RoleModel.id == MembershipModel.role_id)
        .where(
            MembershipModel.user_id == user.id,
            MembershipModel.organization_id == organization.id,
        )
    )
    membership_row = membership_result.one_or_none()
    created_membership = membership_row is None
    if membership_row is None:
        if not created_user:
            raise ValueError(
                "Refusing to grant administrator access to an existing user without "
                "an administrator membership."
            )
        session.add(
            MembershipModel(
                user_id=user.id,
                organization_id=organization.id,
                role_id=role.id,
                status="ACTIVE",
                is_active=True,
            )
        )
    else:
        membership, role_name = membership_row
        is_active_admin = (
            role_name == RoleEnum.ADMIN
            and membership.is_active
            and membership.status == "ACTIVE"
        )
        if not is_active_admin:
            raise ValueError(
                "The existing user membership is not an active administrator membership."
            )

    await session.flush()
    return BootstrapResult(
        user_id=str(user.id),
        organization_id=str(organization.id),
        created_user=created_user,
        created_organization=created_organization,
        created_membership=created_membership,
    )


async def _run_bootstrap() -> BootstrapResult:
    email = os.getenv("BOOTSTRAP_ADMIN_EMAIL") or input("Development admin email: ").strip()
    full_name = os.getenv("BOOTSTRAP_ADMIN_NAME") or input("Development admin name: ").strip()
    password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    if password is None:
        password = getpass("Development admin password: ")
        confirmation = getpass("Confirm password: ")
        if password != confirmation:
            raise ValueError("Passwords do not match.")

    organization_name = os.getenv(
        "BOOTSTRAP_ORGANIZATION_NAME",
        "Development Organization",
    )
    organization_slug = os.getenv("BOOTSTRAP_ORGANIZATION_SLUG", "development")

    async with db_manager.session_scope() as session:
        return await bootstrap_development_admin(
            session,
            email=email,
            password=password,
            full_name=full_name,
            organization_name=organization_name,
            organization_slug=organization_slug,
        )


def main() -> None:
    if settings.ENVIRONMENT.casefold() != "development":
        raise SystemExit("Development administrator bootstrap is disabled outside development.")
    try:
        result = asyncio.run(_run_bootstrap())
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc

    action = "created" if result.created_user else "already exists"
    print(
        f"Development administrator {action}: {result.user_id}; "
        f"organization={result.organization_id}; "
        f"membership={'created' if result.created_membership else 'already exists'}."
    )


if __name__ == "__main__":
    main()
