"""In-memory and relational repository implementations for Operations."""

from typing import Dict, List, Optional
import uuid

from industrial_oracle.operations.application.interfaces import (
    IMaterialConsumptionRepository,
    IProductionRunRepository,
    IWorkOrderRepository,
)
from industrial_oracle.operations.domain.consumption import MaterialConsumption
from industrial_oracle.operations.domain.production_run import ProductionRun
from industrial_oracle.operations.domain.work_order import WorkOrder


class InMemoryWorkOrderRepository(IWorkOrderRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, WorkOrder] = {}

    async def get_by_id(self, work_order_id: uuid.UUID) -> Optional[WorkOrder]:
        return self._storage.get(work_order_id)

    async def get_by_number(self, organization_id: uuid.UUID, work_order_number: str) -> Optional[WorkOrder]:
        return next(
            (
                w
                for w in self._storage.values()
                if w.organization_id == organization_id and w.work_order_number == work_order_number
            ),
            None,
        )

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        work_order_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WorkOrder]:
        orders = [w for w in self._storage.values() if w.organization_id == organization_id]
        if plant_id:
            orders = [w for w in orders if w.plant_id == plant_id]
        if status:
            orders = [w for w in orders if w.status == status]
        if work_order_type:
            orders = [w for w in orders if w.work_order_type == work_order_type]
        orders.sort(key=lambda x: x.created_at, reverse=True)
        return orders[offset : offset + limit]

    async def add(self, work_order: WorkOrder) -> WorkOrder:
        self._storage[work_order.id] = work_order
        return work_order

    async def update(self, work_order: WorkOrder) -> WorkOrder:
        self._storage[work_order.id] = work_order
        return work_order


class InMemoryProductionRunRepository(IProductionRunRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, ProductionRun] = {}

    async def get_by_id(self, run_id: uuid.UUID) -> Optional[ProductionRun]:
        return self._storage.get(run_id)

    async def get_by_number(self, organization_id: uuid.UUID, run_number: str) -> Optional[ProductionRun]:
        return next(
            (
                r
                for r in self._storage.values()
                if r.organization_id == organization_id and r.run_number == run_number
            ),
            None,
        )

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        production_line_id: Optional[uuid.UUID] = None,
        work_order_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProductionRun]:
        runs = [r for r in self._storage.values() if r.organization_id == organization_id]
        if production_line_id:
            runs = [r for r in runs if r.production_line_id == production_line_id]
        if work_order_id:
            runs = [r for r in runs if r.work_order_id == work_order_id]
        if status:
            runs = [r for r in runs if r.status == status]
        runs.sort(key=lambda x: x.created_at, reverse=True)
        return runs[offset : offset + limit]

    async def add(self, run: ProductionRun) -> ProductionRun:
        self._storage[run.id] = run
        return run

    async def update(self, run: ProductionRun) -> ProductionRun:
        self._storage[run.id] = run
        return run


class InMemoryMaterialConsumptionRepository(IMaterialConsumptionRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, MaterialConsumption] = {}

    async def add(self, consumption: MaterialConsumption) -> MaterialConsumption:
        self._storage[consumption.id] = consumption
        return consumption

    async def list_by_consumer(
        self,
        organization_id: uuid.UUID,
        consumer_type: str,
        consumer_id: uuid.UUID,
    ) -> List[MaterialConsumption]:
        return [
            c
            for c in self._storage.values()
            if c.organization_id == organization_id
            and c.consumer_type == consumer_type
            and c.consumer_id == consumer_id
        ]


# Singleton in-memory instances
work_order_repo = InMemoryWorkOrderRepository()
production_run_repo = InMemoryProductionRunRepository()
material_consumption_repo = InMemoryMaterialConsumptionRepository()
