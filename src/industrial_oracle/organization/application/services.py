"""Organization application service."""

from typing import List, Optional
import uuid

from industrial_oracle.organization.application.dtos import (
    OrganizationResponseDTO,
    PlantResponseDTO,
    SiteResponseDTO,
)
from industrial_oracle.organization.application.interfaces import (
    IMembershipRepository,
    IOrganizationRepository,
    IPlantRepository,
    ISiteRepository,
)


class OrganizationService:
    """Coordinates organizational queries and physical plant hierarchy navigation."""

    def __init__(
        self,
        org_repo: IOrganizationRepository,
        membership_repo: IMembershipRepository,
        site_repo: ISiteRepository,
        plant_repo: IPlantRepository,
    ) -> None:
        self.org_repo = org_repo
        self.membership_repo = membership_repo
        self.site_repo = site_repo
        self.plant_repo = plant_repo

    async def list_user_organizations(self, user_id: uuid.UUID) -> List[OrganizationResponseDTO]:
        """Lists organizations the given user has active membership in."""
        memberships = await self.membership_repo.list_user_memberships(user_id)
        results: List[OrganizationResponseDTO] = []

        for m in memberships:
            if not m.is_active:
                continue
            org = await self.org_repo.get_by_id(m.organization_id)
            if org and org.status == "ACTIVE":
                results.append(
                    OrganizationResponseDTO(
                        id=org.id,
                        name=org.name,
                        slug=org.slug,
                        status=org.status,
                        role_in_org=m.role,
                        created_at=org.created_at,
                        updated_at=org.updated_at,
                    )
                )
        return results

    async def list_sites(self, organization_id: uuid.UUID) -> List[SiteResponseDTO]:
        """Lists sites belonging strictly to the specified tenant organization."""
        sites = await self.site_repo.list_by_organization(organization_id)
        return [
            SiteResponseDTO(
                id=s.id,
                organization_id=s.organization_id,
                name=s.name,
                code=s.code,
                address=s.address,
                timezone=s.timezone,
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
            for s in sites
        ]

    async def list_plants(
        self,
        organization_id: uuid.UUID,
        site_id: Optional[uuid.UUID] = None,
    ) -> List[PlantResponseDTO]:
        """Lists plants belonging strictly to the specified tenant organization."""
        plants = await self.plant_repo.list_by_organization(organization_id, site_id=site_id)
        return [
            PlantResponseDTO(
                id=p.id,
                organization_id=p.organization_id,
                site_id=p.site_id,
                name=p.name,
                code=p.code,
                status=p.status,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in plants
        ]
