"""Identity repository interfaces."""

from abc import abstractmethod
from typing import List, Optional
import uuid

from industrial_oracle.identity.domain.models import User
from industrial_oracle.shared.application.repository import GenericRepository


class IUserRepository(GenericRepository[User, uuid.UUID]):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_organization(self, organization_id: uuid.UUID) -> List[User]:
        raise NotImplementedError
