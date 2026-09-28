"""Organization, Membership, Site, and Plant repository implementations."""

from typing import Dict, List, Optional
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from industrial_oracle.core.exceptions import EntityNotFoundException
from industrial_oracle.identity.infrastructure.models import RoleModel
from industrial_oracle.organization.application.interfaces import (
    IMembershipRepository,
    IOrganizationRepository,
    IPlantRepository,
    ISiteRepository,
)
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site
from industrial_oracle.organization.infrastructure.models import (
    MembershipModel,
    OrganizationModel,
    PlantModel,
    SiteModel,
)


class PostgreSQLOrganizationRepository(IOrganizationRepository):
    """Persists organization entities through the request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: OrganizationModel) -> Organization:
        return Organization(
            id=model.id,
            name=model.name,
            slug=model.slug,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Organization]:
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        result = await self.session.execute(
            select(OrganizationModel).where(OrganizationModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def list(
        self,
        organization_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict] = None,
    ) -> List[Organization]:
        result = await self.session.execute(
            select(OrganizationModel)
            .where(OrganizationModel.id == organization_id)
            .order_by(OrganizationModel.created_at, OrganizationModel.id)
            .offset(offset)
            .limit(limit)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def add(self, entity: Organization) -> Organization:
        model = OrganizationModel(
            id=entity.id,
            name=entity.name,
            slug=entity.slug,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def update(self, entity: Organization) -> Organization:
        model = await self.session.get(OrganizationModel, entity.id)
        if model is None:
            raise EntityNotFoundException("Organization", entity.id)
        model.name = entity.name
        model.slug = entity.slug
        model.status = entity.status
        model.updated_at = entity.updated_at
        await self.session.flush()
        return self._to_domain(model)

    async def delete(self, entity_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(OrganizationModel).where(OrganizationModel.id == entity_id)
        )
        return bool(result.rowcount)


class PostgreSQLMembershipRepository(IMembershipRepository):
    """Persists memberships and resolves their role names from the existing role table."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: MembershipModel, role_name: str) -> Membership:
        return Membership(
            id=model.id,
            user_id=model.user_id,
            organization_id=model.organization_id,
            role=role_name,
            status=model.status,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def _get_membership(
        self,
        *conditions: object,
    ) -> Optional[Membership]:
        result = await self.session.execute(
            select(MembershipModel, RoleModel.name)
            .join(RoleModel, RoleModel.id == MembershipModel.role_id)
            .where(*conditions)
        )
        row = result.one_or_none()
        return self._to_domain(row[0], row[1]) if row is not None else None

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Membership]:
        return await self._get_membership(MembershipModel.id == entity_id)

    async def get_user_membership(
        self,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> Optional[Membership]:
        return await self._get_membership(
            MembershipModel.user_id == user_id,
            MembershipModel.organization_id == org_id,
        )

    async def list_user_memberships(self, user_id: uuid.UUID) -> List[Membership]:
        result = await self.session.execute(
            select(MembershipModel, RoleModel.name)
            .join(RoleModel, RoleModel.id == MembershipModel.role_id)
            .where(MembershipModel.user_id == user_id)
            .order_by(MembershipModel.created_at, MembershipModel.id)
        )
        return [
            self._to_domain(row[0], row[1])
            for row in result.all()
        ]

    async def list_org_memberships(self, org_id: uuid.UUID) -> List[Membership]:
        result = await self.session.execute(
            select(MembershipModel, RoleModel.name)
            .join(RoleModel, RoleModel.id == MembershipModel.role_id)
            .where(MembershipModel.organization_id == org_id)
            .order_by(MembershipModel.created_at, MembershipModel.id)
        )
        return [self._to_domain(row[0], row[1]) for row in result.all()]

    async def list(
        self,
        organization_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict] = None,
    ) -> List[Membership]:
        result = await self.session.execute(
            select(MembershipModel, RoleModel.name)
            .join(RoleModel, RoleModel.id == MembershipModel.role_id)
            .where(MembershipModel.organization_id == organization_id)
            .order_by(MembershipModel.created_at, MembershipModel.id)
            .offset(offset)
            .limit(limit)
        )
        return [self._to_domain(row[0], row[1]) for row in result.all()]

    async def add(self, entity: Membership) -> Membership:
        role_result = await self.session.execute(
            select(RoleModel.id).where(RoleModel.name == entity.role)
        )
        role_id = role_result.scalar_one_or_none()
        if role_id is None:
            raise EntityNotFoundException("Role", entity.role)

        model = MembershipModel(
            id=entity.id,
            user_id=entity.user_id,
            organization_id=entity.organization_id,
            role_id=role_id,
            status=entity.status,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model, entity.role)

    async def update(self, entity: Membership) -> Membership:
        model = await self.session.get(MembershipModel, entity.id)
        if model is None:
            raise EntityNotFoundException("Membership", entity.id)

        role_result = await self.session.execute(
            select(RoleModel.id).where(RoleModel.name == entity.role)
        )
        role_id = role_result.scalar_one_or_none()
        if role_id is None:
            raise EntityNotFoundException("Role", entity.role)
        model.user_id = entity.user_id
        model.organization_id = entity.organization_id
        model.role_id = role_id
        model.status = entity.status
        model.is_active = entity.is_active
        model.updated_at = entity.updated_at
        await self.session.flush()
        return self._to_domain(model, entity.role)

    async def delete(self, entity_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(MembershipModel).where(MembershipModel.id == entity_id)
        )
        return bool(result.rowcount)


class PostgreSQLSiteRepository(ISiteRepository):
    """Queries site records scoped to their owning organization."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: SiteModel) -> Site:
        return Site(
            id=model.id,
            organization_id=model.organization_id,
            name=model.name,
            code=model.code,
            address=model.address,
            timezone_str=model.timezone,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Site]:
        result = await self.session.execute(select(SiteModel).where(SiteModel.id == entity_id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def list_by_organization(self, org_id: uuid.UUID) -> List[Site]:
        result = await self.session.execute(
            select(SiteModel)
            .where(SiteModel.organization_id == org_id)
            .order_by(SiteModel.created_at, SiteModel.id)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list(
        self,
        organization_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict] = None,
    ) -> List[Site]:
        result = await self.session.execute(
            select(SiteModel)
            .where(SiteModel.organization_id == organization_id)
            .order_by(SiteModel.created_at, SiteModel.id)
            .offset(offset)
            .limit(limit)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def add(self, entity: Site) -> Site:
        model = SiteModel(
            id=entity.id,
            organization_id=entity.organization_id,
            name=entity.name,
            code=entity.code,
            address=entity.address,
            timezone=entity.timezone,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def update(self, entity: Site) -> Site:
        model = await self.session.get(SiteModel, entity.id)
        if model is None:
            raise EntityNotFoundException("Site", entity.id)
        model.organization_id = entity.organization_id
        model.name = entity.name
        model.code = entity.code
        model.address = entity.address
        model.timezone = entity.timezone
        model.updated_at = entity.updated_at
        await self.session.flush()
        return self._to_domain(model)

    async def delete(self, entity_id: uuid.UUID) -> bool:
        result = await self.session.execute(delete(SiteModel).where(SiteModel.id == entity_id))
        return bool(result.rowcount)


class PostgreSQLPlantRepository(IPlantRepository):
    """Queries plant records scoped to their owning organization and optional site."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: PlantModel) -> Plant:
        return Plant(
            id=model.id,
            organization_id=model.organization_id,
            site_id=model.site_id,
            name=model.name,
            code=model.code,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Plant]:
        result = await self.session.execute(select(PlantModel).where(PlantModel.id == entity_id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def list_by_organization(
        self,
        org_id: uuid.UUID,
        site_id: Optional[uuid.UUID] = None,
    ) -> List[Plant]:
        query = select(PlantModel).where(PlantModel.organization_id == org_id)
        if site_id is not None:
            query = query.where(PlantModel.site_id == site_id)
        result = await self.session.execute(query.order_by(PlantModel.created_at, PlantModel.id))
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list(
        self,
        organization_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict] = None,
    ) -> List[Plant]:
        result = await self.session.execute(
            select(PlantModel)
            .where(PlantModel.organization_id == organization_id)
            .order_by(PlantModel.created_at, PlantModel.id)
            .offset(offset)
            .limit(limit)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def add(self, entity: Plant) -> Plant:
        model = PlantModel(
            id=entity.id,
            organization_id=entity.organization_id,
            site_id=entity.site_id,
            name=entity.name,
            code=entity.code,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def update(self, entity: Plant) -> Plant:
        model = await self.session.get(PlantModel, entity.id)
        if model is None:
            raise EntityNotFoundException("Plant", entity.id)
        model.organization_id = entity.organization_id
        model.site_id = entity.site_id
        model.name = entity.name
        model.code = entity.code
        model.status = entity.status
        model.updated_at = entity.updated_at
        await self.session.flush()
        return self._to_domain(model)

    async def delete(self, entity_id: uuid.UUID) -> bool:
        result = await self.session.execute(delete(PlantModel).where(PlantModel.id == entity_id))
        return bool(result.rowcount)


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
