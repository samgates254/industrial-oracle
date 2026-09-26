"""Organization domain models."""

from datetime import datetime, timezone
from typing import Optional
import uuid

from industrial_oracle.shared.domain.entity import AggregateRoot, Entity


class Organization(AggregateRoot):
    """Enterprise multi-tenant boundary aggregate root."""

    def __init__(
        self,
        name: str,
        slug: str,
        id: Optional[uuid.UUID] = None,
        status: str = "ACTIVE",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.name = name
        self.slug = slug
        self.status = status


class Membership(Entity):
    """Associates a User with an Organization and defines their Role within it."""

    def __init__(
        self,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        role: str,
        id: Optional[uuid.UUID] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.user_id = user_id
        self.organization_id = organization_id
        self.role = role
        self.is_active = is_active

    def change_role(self, new_role: str) -> None:
        self.role = new_role
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)


class Site(Entity):
    """Physical geographic industrial complex."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        name: str,
        code: str,
        address: Optional[str] = None,
        timezone_str: str = "UTC",
        id: Optional[uuid.UUID] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.name = name
        self.code = code
        self.address = address
        self.timezone = timezone_str


class Plant(Entity):
    """Operational manufacturing or processing plant."""

    def __init__(
        self,
        organization_id: uuid.UUID,
        site_id: uuid.UUID,
        name: str,
        code: str,
        id: Optional[uuid.UUID] = None,
        status: str = "OPERATIONAL",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        super().__init__(id=id, created_at=created_at, updated_at=updated_at)
        self.organization_id = organization_id
        self.site_id = site_id
        self.name = name
        self.code = code
        self.status = status
