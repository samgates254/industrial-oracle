"""Organization repository interfaces."""

from abc import abstractmethod
from typing import List, Optional
import uuid

from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site
from industrial_oracle.shared.application.repository import GenericRepository


class IOrganizationRepository(GenericRepository[Organization, uuid.UUID]):
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        raise NotImplementedError


class IMembershipRepository(GenericRepository[Membership, uuid.UUID]):
    @abstractmethod
    async def get_user_membership(self, user_id: uuid.UUID, org_id: uuid.UUID) -> Optional[Membership]:
        raise NotImplementedError

    @abstractmethod
    async def list_user_memberships(self, user_id: uuid.UUID) -> List[Membership]:
        raise NotImplementedError

    @abstractmethod
    async def list_org_memberships(self, org_id: uuid.UUID) -> List[Membership]:
        raise NotImplementedError


class ISiteRepository(GenericRepository[Site, uuid.UUID]):
    @abstractmethod
    async def list_by_organization(self, org_id: uuid.UUID) -> List[Site]:
        raise NotImplementedError


class IPlantRepository(GenericRepository[Plant, uuid.UUID]):
    @abstractmethod
    async def list_by_organization(self, org_id: uuid.UUID, site_id: Optional[uuid.UUID] = None) -> List[Plant]:
        raise NotImplementedError
