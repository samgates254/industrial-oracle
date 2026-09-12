"""Organization, Membership, Site, and Plant repository implementations."""

from typing import Dict, List, Optional
import uuid

from industrial_oracle.organization.application.interfaces import (
    IMembershipRepository,
    IOrganizationRepository,
    IPlantRepository,
    ISiteRepository,
)
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site


class InMemoryOrganizationRepository(IOrganizationRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, Organization] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Organization]:
        return self._storage.get(entity_id)

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        return next((o for o in self._storage.values() if o.slug == slug), None)

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[Organization]:
        return list(self._storage.values())[offset : offset + limit]

    async def add(self, entity: Organization) -> Organization:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: Organization) -> Organization:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


class InMemoryMembershipRepository(IMembershipRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, Membership] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Membership]:
        return self._storage.get(entity_id)

    async def get_user_membership(self, user_id: uuid.UUID, org_id: uuid.UUID) -> Optional[Membership]:
        return next(
            (m for m in self._storage.values() if m.user_id == user_id and m.organization_id == org_id),
            None,
        )

    async def list_user_memberships(self, user_id: uuid.UUID) -> List[Membership]:
        return [m for m in self._storage.values() if m.user_id == user_id]

    async def list_org_memberships(self, org_id: uuid.UUID) -> List[Membership]:
        return [m for m in self._storage.values() if m.organization_id == org_id]

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[Membership]:
        return [m for m in self._storage.values() if m.organization_id == organization_id][offset : offset + limit]

    async def add(self, entity: Membership) -> Membership:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: Membership) -> Membership:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


class InMemorySiteRepository(ISiteRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, Site] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Site]:
        return self._storage.get(entity_id)

    async def list_by_organization(self, org_id: uuid.UUID) -> List[Site]:
        return [s for s in self._storage.values() if s.organization_id == org_id]

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[Site]:
        return await self.list_by_organization(organization_id)

    async def add(self, entity: Site) -> Site:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: Site) -> Site:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


class InMemoryPlantRepository(IPlantRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, Plant] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Plant]:
        return self._storage.get(entity_id)

    async def list_by_organization(self, org_id: uuid.UUID, site_id: Optional[uuid.UUID] = None) -> List[Plant]:
        plants = [p for p in self._storage.values() if p.organization_id == org_id]
        if site_id:
            plants = [p for p in plants if p.site_id == site_id]
        return plants

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[Plant]:
        return await self.list_by_organization(organization_id)

    async def add(self, entity: Plant) -> Plant:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: Plant) -> Plant:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


# Global singletons
organization_repo = InMemoryOrganizationRepository()
membership_repo = InMemoryMembershipRepository()
site_repo = InMemorySiteRepository()
plant_repo = InMemoryPlantRepository()
