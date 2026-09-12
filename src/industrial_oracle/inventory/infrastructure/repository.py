"""In-memory and relational repository implementations for Inventory."""

import asyncio
from typing import Dict, List, Optional, Tuple
import uuid

from industrial_oracle.inventory.application.interfaces import (
    IInventoryBalanceRepository,
    IInventoryLocationRepository,
    IInventoryTransactionRepository,
    IItemRepository,
)
from industrial_oracle.inventory.domain.models import (
    InventoryBalance,
    InventoryLocation,
    InventoryTransaction,
    Item,
)


class InMemoryItemRepository(IItemRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, Item] = {}

    async def get_by_id(self, item_id: uuid.UUID) -> Optional[Item]:
        return self._storage.get(item_id)

    async def get_by_sku(self, organization_id: uuid.UUID, sku: str) -> Optional[Item]:
        clean_sku = sku.strip().upper()
        return next(
            (i for i in self._storage.values() if i.organization_id == organization_id and i.sku == clean_sku),
            None,
        )

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        category: Optional[str] = None,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Item]:
        items = [i for i in self._storage.values() if i.organization_id == organization_id]
        if active_only:
            items = [i for i in items if i.active]
        if category:
            items = [i for i in items if i.category == category]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[offset : offset + limit]

    async def add(self, item: Item) -> Item:
        self._storage[item.id] = item
        return item

    async def update(self, item: Item) -> Item:
        self._storage[item.id] = item
        return item


class InMemoryInventoryLocationRepository(IInventoryLocationRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, InventoryLocation] = {}

    async def get_by_id(self, location_id: uuid.UUID) -> Optional[InventoryLocation]:
        return self._storage.get(location_id)

    async def get_by_code(
        self, organization_id: uuid.UUID, site_id: uuid.UUID, code: str
    ) -> Optional[InventoryLocation]:
        clean_code = code.strip().upper()
        return next(
            (
                loc
                for loc in self._storage.values()
                if loc.organization_id == organization_id
                and loc.site_id == site_id
                and loc.code == clean_code
            ),
            None,
        )

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        site_id: Optional[uuid.UUID] = None,
        plant_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InventoryLocation]:
        locations = [loc for loc in self._storage.values() if loc.organization_id == organization_id]
        if site_id:
            locations = [loc for loc in locations if loc.site_id == site_id]
        if plant_id:
            locations = [loc for loc in locations if loc.plant_id == plant_id]
        locations.sort(key=lambda x: x.created_at, reverse=True)
        return locations[offset : offset + limit]

    async def add(self, location: InventoryLocation) -> InventoryLocation:
        self._storage[location.id] = location
        return location


class InMemoryInventoryBalanceRepository(IInventoryBalanceRepository):
    def __init__(self) -> None:
        self._storage: Dict[Tuple[uuid.UUID, uuid.UUID, uuid.UUID], InventoryBalance] = {}
        self._lock = asyncio.Lock()

    async def get_by_item_and_location(
        self,
        organization_id: uuid.UUID,
        item_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> Optional[InventoryBalance]:
        key = (organization_id, item_id, location_id)
        return self._storage.get(key)

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        item_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InventoryBalance]:
        balances = [b for b in self._storage.values() if b.organization_id == organization_id]
        if item_id:
            balances = [b for b in balances if b.item_id == item_id]
        if location_id:
            balances = [b for b in balances if b.location_id == location_id]
        balances.sort(key=lambda x: x.created_at, reverse=True)
        return balances[offset : offset + limit]

    async def add(self, balance: InventoryBalance) -> InventoryBalance:
        async with self._lock:
            key = (balance.organization_id, balance.item_id, balance.location_id)
            self._storage[key] = balance
            return balance

    async def update(self, balance: InventoryBalance) -> InventoryBalance:
        async with self._lock:
            key = (balance.organization_id, balance.item_id, balance.location_id)
            self._storage[key] = balance
            return balance


class InMemoryInventoryTransactionRepository(IInventoryTransactionRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, InventoryTransaction] = {}

    async def add(self, transaction: InventoryTransaction) -> InventoryTransaction:
        self._storage[transaction.id] = transaction
        return transaction

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        item_id: Optional[uuid.UUID] = None,
        location_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InventoryTransaction]:
        txs = [t for t in self._storage.values() if t.organization_id == organization_id]
        if item_id:
            txs = [t for t in txs if t.item_id == item_id]
        if location_id:
            txs = [t for t in txs if t.location_id == location_id]
        txs.sort(key=lambda x: x.created_at, reverse=True)
        return txs[offset : offset + limit]


# Singleton repository instances
item_repo = InMemoryItemRepository()
inventory_location_repo = InMemoryInventoryLocationRepository()
inventory_balance_repo = InMemoryInventoryBalanceRepository()
inventory_transaction_repo = InMemoryInventoryTransactionRepository()
