"""Repository interfaces for Maintenance bounded context."""

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from industrial_oracle.maintenance.domain.maintenance_order import MaintenanceWorkOrder


class IMaintenanceOrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, maintenance_id: uuid.UUID) -> Optional[MaintenanceWorkOrder]:
        pass

    @abstractmethod
    async def get_by_work_order_id(self, work_order_id: uuid.UUID) -> Optional[MaintenanceWorkOrder]:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        asset_id: Optional[uuid.UUID] = None,
        machine_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MaintenanceWorkOrder]:
        pass

    @abstractmethod
    async def add(self, order: MaintenanceWorkOrder) -> MaintenanceWorkOrder:
        pass

    @abstractmethod
    async def update(self, order: MaintenanceWorkOrder) -> MaintenanceWorkOrder:
        pass
