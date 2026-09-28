from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import uuid

import pytest

from industrial_oracle.organization.infrastructure.models import OrganizationModel
from industrial_oracle.organization.infrastructure.repository import (
    PostgreSQLOrganizationRepository,
    PostgreSQLPlantRepository,
)


@pytest.mark.asyncio
async def test_postgresql_organization_repository_maps_existing_organization() -> None:
    now = datetime.now(timezone.utc)
    model = OrganizationModel(
        id=uuid.uuid4(),
        name="Example Organization",
        slug="example-organization",
        status="ACTIVE",
        created_at=now,
        updated_at=now,
    )
    result = SimpleNamespace(scalar_one_or_none=lambda: model)
    session = Mock()
    session.execute = AsyncMock(return_value=result)

    organization = await PostgreSQLOrganizationRepository(session).get_by_slug(
        "example-organization"
    )

    assert organization is not None
    assert organization.id == model.id
    assert organization.name == model.name
    assert organization.slug == model.slug
    assert organization.status == model.status
    assert organization.created_at == model.created_at


@pytest.mark.asyncio
async def test_postgresql_plant_list_filters_by_organization_and_site() -> None:
    organization_id = uuid.uuid4()
    site_id = uuid.uuid4()
    session = Mock()
    session.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: [])
        )
    )

    await PostgreSQLPlantRepository(session).list_by_organization(
        organization_id,
        site_id=site_id,
    )

    statement = str(session.execute.await_args.args[0])
    assert "plants.organization_id" in statement
    assert "plants.site_id" in statement


@pytest.mark.asyncio
async def test_postgresql_organization_list_is_scoped_to_requested_id() -> None:
    organization_id = uuid.uuid4()
    session = Mock()
    session.execute = AsyncMock(
        return_value=SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=lambda: [])
        )
    )

    organizations = await PostgreSQLOrganizationRepository(session).list(organization_id)

    assert organizations == []
    statement = session.execute.await_args.args[0]
    assert "organizations.id" in str(statement)
    assert organization_id in statement.compile().params.values()
