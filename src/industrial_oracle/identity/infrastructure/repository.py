"""Identity repository implementations."""

from typing import Dict, List, Optional
import uuid

from industrial_oracle.identity.application.interfaces import IUserRepository
from industrial_oracle.identity.domain.models import User
from industrial_oracle.organization.infrastructure.repository import membership_repo


class InMemoryUserRepository(IUserRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, User] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[User]:
        return self._storage.get(entity_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        clean = email.strip().lower()
        return next((u for u in self._storage.values() if u.email == clean), None)

    async def list_by_organization(self, organization_id: uuid.UUID) -> List[User]:
        memberships = await membership_repo.list_org_memberships(organization_id)
        user_ids = {m.user_id for m in memberships}
        return [u for u in self._storage.values() if u.id in user_ids]

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[User]:
        return (await self.list_by_organization(organization_id))[offset : offset + limit]

    async def add(self, entity: User) -> User:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: User) -> User:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


# Global singleton repository
user_repo = InMemoryUserRepository()
