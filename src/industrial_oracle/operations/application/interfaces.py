"""Repository interfaces for Operations bounded context."""

from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from industrial_oracle.operations.domain.consumption import MaterialConsumption
from industrial_oracle.operations.domain.production_run import ProductionRun
from industrial_oracle.operations.domain.work_order import WorkOrder


class IWorkOrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, work_order_id: uuid.UUID) -> Optional[WorkOrder]:
        pass

    @abstractmethod
    async def get_by_number(self, organization_id: uuid.UUID, work_order_number: str) -> Optional[WorkOrder]:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        work_order_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WorkOrder]:
        pass

    @abstractmethod
    async def add(self, work_order: WorkOrder) -> WorkOrder:
        pass

    @abstractmethod
    async def update(self, work_order: WorkOrder) -> WorkOrder:
        pass


class IProductionRunRepository(ABC):
    @abstractmethod
    async def get_by_id(self, run_id: uuid.UUID) -> Optional[ProductionRun]:
        pass

    @abstractmethod
    async def get_by_number(self, organization_id: uuid.UUID, run_number: str) -> Optional[ProductionRun]:
        pass

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        production_line_id: Optional[uuid.UUID] = None,
        work_order_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProductionRun]:
        pass

    @abstractmethod
    async def add(self, run: ProductionRun) -> ProductionRun:
        pass

    @abstractmethod
    async def update(self, run: ProductionRun) -> ProductionRun:
        pass


class IMaterialConsumptionRepository(ABC):
    @abstractmethod
    async def add(self, consumption: MaterialConsumption) -> MaterialConsumption:
        pass

    @abstractmethod
    async def list_by_consumer(
        self,
        organization_id: uuid.UUID,
        consumer_type: str,
        consumer_id: uuid.UUID,
    ) -> List[MaterialConsumption]:
        pass
