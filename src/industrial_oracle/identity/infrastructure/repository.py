"""Identity repository implementations."""

from typing import Dict, List, Optional
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from industrial_oracle.core.exceptions import EntityNotFoundException
from industrial_oracle.identity.application.interfaces import IUserRepository
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.models import UserModel
from industrial_oracle.organization.infrastructure.models import MembershipModel
from industrial_oracle.organization.infrastructure.repository import membership_repo


class PostgreSQLUserRepository(IUserRepository):
    """Persists user domain entities through the request-scoped SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _to_domain(model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            full_name=model.full_name,
            is_active=model.is_active,
            is_superuser=model.is_superuser,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def get_by_email(self, email: str) -> Optional[User]:
        clean_email = email.strip().lower()
        result = await self.session.execute(
            select(UserModel).where(func.lower(UserModel.email) == clean_email)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model is not None else None

    async def list_by_organization(self, organization_id: uuid.UUID) -> List[User]:
        result = await self.session.execute(
            select(UserModel)
            .join(MembershipModel, MembershipModel.user_id == UserModel.id)
            .where(MembershipModel.organization_id == organization_id)
            .order_by(UserModel.created_at, UserModel.id)
        )
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list(
        self,
        organization_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict] = None,
    ) -> List[User]:
        return (await self.list_by_organization(organization_id))[offset : offset + limit]

    async def add(self, entity: User) -> User:
        model = UserModel(
            id=entity.id,
            email=entity.email,
            password_hash=entity.password_hash,
            full_name=entity.full_name,
            is_active=entity.is_active,
            is_superuser=entity.is_superuser,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    async def update(self, entity: User) -> User:
        model = await self.session.get(UserModel, entity.id)
        if model is None:
            raise EntityNotFoundException("User", entity.id)
        model.email = entity.email
        model.password_hash = entity.password_hash
        model.full_name = entity.full_name
        model.is_active = entity.is_active
        model.is_superuser = entity.is_superuser
        model.updated_at = entity.updated_at
        await self.session.flush()
        return self._to_domain(model)

    async def delete(self, entity_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(UserModel).where(UserModel.id == entity_id)
        )
        return bool(result.rowcount)


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
