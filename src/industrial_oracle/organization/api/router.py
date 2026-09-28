"""Organization and physical facilities API endpoints."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from industrial_oracle.core.security import (
    PermissionEnum,
    TenantContext,
    get_current_user,
    get_tenant_context,
    require_permission,
)
from industrial_oracle.core.database import get_db
from industrial_oracle.organization.application.dtos import (
    OrganizationResponseDTO,
    PlantResponseDTO,
    SiteResponseDTO,
)
from industrial_oracle.organization.application.services import OrganizationService
from industrial_oracle.organization.infrastructure.repository import (
    PostgreSQLMembershipRepository,
    PostgreSQLOrganizationRepository,
    PostgreSQLPlantRepository,
    PostgreSQLSiteRepository,
)

router = APIRouter(prefix="/api/v1", tags=["Organization & Facilities"])


def get_organization_service(session: AsyncSession = Depends(get_db)) -> OrganizationService:
    return OrganizationService(
        PostgreSQLOrganizationRepository(session),
        PostgreSQLMembershipRepository(session),
        PostgreSQLSiteRepository(session),
        PostgreSQLPlantRepository(session),
    )


@router.get("/organizations", response_model=List[OrganizationResponseDTO])
async def get_my_organizations(
    current_user=Depends(get_current_user),
    org_service: OrganizationService = Depends(get_organization_service),
):
    """Lists all organizations in which the authenticated user has active membership."""
    return await org_service.list_user_organizations(current_user.id)


@router.get(
    "/sites",
    response_model=List[SiteResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.ORGANIZATION_READ))],
)
async def get_sites(
    ctx: TenantContext = Depends(get_tenant_context),
    org_service: OrganizationService = Depends(get_organization_service),
):
    """Retrieves physical sites belonging strictly to the authenticated tenant organization."""
    return await org_service.list_sites(ctx.organization.id)


@router.get(
    "/plants",
    response_model=List[PlantResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.ORGANIZATION_READ))],
)
async def get_plants(
    site_id: Optional[uuid.UUID] = Query(None, description="Optional site filter"),
    ctx: TenantContext = Depends(get_tenant_context),
    org_service: OrganizationService = Depends(get_organization_service),
):
    """Retrieves plants belonging strictly to the authenticated tenant organization."""
    return await org_service.list_plants(ctx.organization.id, site_id=site_id)
