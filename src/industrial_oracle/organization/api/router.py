"""Organization and physical facilities API endpoints."""

from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, Query

from industrial_oracle.core.security import (
    PermissionEnum,
    TenantContext,
    get_current_user,
    get_tenant_context,
    require_permission,
)
from industrial_oracle.organization.application.dtos import (
    OrganizationResponseDTO,
    PlantResponseDTO,
    SiteResponseDTO,
)
from industrial_oracle.organization.application.services import OrganizationService
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
    plant_repo,
    site_repo,
)

router = APIRouter(prefix="/api/v1", tags=["Organization & Facilities"])
org_service = OrganizationService(organization_repo, membership_repo, site_repo, plant_repo)


@router.get("/organizations", response_model=List[OrganizationResponseDTO])
async def get_my_organizations(current_user=Depends(get_current_user)):
    """Lists all organizations in which the authenticated user has active membership."""
    return await org_service.list_user_organizations(current_user.id)


@router.get(
    "/sites",
    response_model=List[SiteResponseDTO],
    dependencies=[Depends(require_permission(PermissionEnum.ORGANIZATION_READ))],
)
async def get_sites(ctx: TenantContext = Depends(get_tenant_context)):
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
):
    """Retrieves plants belonging strictly to the authenticated tenant organization."""
    return await org_service.list_plants(ctx.organization.id, site_id=site_id)
