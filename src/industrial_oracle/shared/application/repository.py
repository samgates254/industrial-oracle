"""Generic Repository pattern interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, TypeVar
import uuid

T = TypeVar("T")
ID = TypeVar("ID", bound=uuid.UUID)


class GenericRepository(ABC, Generic[T, ID]):
    """Abstract interface for entity persistence."""

    @abstractmethod
    async def get_by_id(self, entity_id: ID) -> Optional[T]:
        """Finds entity by unique primary key."""
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        organization_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
        filters: Optional[dict] = None,
    ) -> List[T]:
        """Lists entities for a given organization."""
        raise NotImplementedError

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Persists a new entity."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Updates an existing entity."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: ID) -> bool:
        """Deletes an entity by identifier."""
        raise NotImplementedError
