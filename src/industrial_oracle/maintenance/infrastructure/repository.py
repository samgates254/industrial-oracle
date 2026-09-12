"""In-memory and relational repository implementations for Maintenance."""

from typing import Dict, List, Optional
import uuid

from industrial_oracle.maintenance.application.interfaces import IMaintenanceOrderRepository
from industrial_oracle.maintenance.domain.maintenance_order import MaintenanceWorkOrder


class InMemoryMaintenanceOrderRepository(IMaintenanceOrderRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, MaintenanceWorkOrder] = {}

    async def get_by_id(self, maintenance_id: uuid.UUID) -> Optional[MaintenanceWorkOrder]:
        return self._storage.get(maintenance_id)

    async def get_by_work_order_id(self, work_order_id: uuid.UUID) -> Optional[MaintenanceWorkOrder]:
        return next((m for m in self._storage.values() if m.work_order_id == work_order_id), None)

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        asset_id: Optional[uuid.UUID] = None,
        machine_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MaintenanceWorkOrder]:
        orders = [m for m in self._storage.values() if m.organization_id == organization_id]
        if asset_id:
            orders = [m for m in orders if m.asset_id == asset_id]
        if machine_id:
            orders = [m for m in orders if m.machine_id == machine_id]
        if status:
            orders = [m for m in orders if m.status == status]
        orders.sort(key=lambda x: x.created_at, reverse=True)
        return orders[offset : offset + limit]

    async def add(self, order: MaintenanceWorkOrder) -> MaintenanceWorkOrder:
        self._storage[order.id] = order
        return order

    async def update(self, order: MaintenanceWorkOrder) -> MaintenanceWorkOrder:
        self._storage[order.id] = order
        return order


# Singleton repository instance
maintenance_order_repo = InMemoryMaintenanceOrderRepository()
