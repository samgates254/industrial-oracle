"""Repository interfaces for Inventory bounded context."""

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from industrial_oracle.inventory.domain.models import (
    InventoryBalance,
    InventoryLocation,
    InventoryTransaction,
    Item,
)


class IItemRepository(ABC):
    @abstractmethod
    async def get_by_id(self, item_id: uuid.UUID) -> Optional[Item]:
        pass

    @abstractmethod
    async def get_by_sku(self, organization_id: uuid.UUID, sku: str) -> Optional[Item]:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        category: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Item]:
        pass

    @abstractmethod
    async def add(self, item: Item) -> Item:
        pass

    @abstractmethod
    async def update(self, item: Item) -> Item:
        pass


class IInventoryLocationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, location_id: uuid.UUID) -> Optional[InventoryLocation]:
        pass

    @abstractmethod
    async def get_by_code(self, organization_id: uuid.UUID, site_id: uuid.UUID, code: str) -> Optional[InventoryLocation]:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        site_id: Optional[uuid.UUID] = None,
        plant_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InventoryLocation]:
        pass

    @abstractmethod
    async def add(self, location: InventoryLocation) -> InventoryLocation:
        pass


class IInventoryBalanceRepository(ABC):
    @abstractmethod
    async def get_by_item_and_location(
        self,
        organization_id: uuid.UUID,
        item_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> Optional[InventoryBalance]:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        item_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InventoryBalance]:
        pass

    @abstractmethod
    async def add(self, balance: InventoryBalance) -> InventoryBalance:
        pass

    @abstractmethod
    async def update(self, balance: InventoryBalance) -> InventoryBalance:
        pass


class IInventoryTransactionRepository(ABC):
    @abstractmethod
    async def add(self, transaction: InventoryTransaction) -> InventoryTransaction:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        item_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InventoryTransaction]:
        pass
