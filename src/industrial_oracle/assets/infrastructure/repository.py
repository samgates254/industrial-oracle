"""Asset, Production Line, Machine, and Telemetry repository implementations."""

from typing import Dict, List, Optional
import uuid

from industrial_oracle.assets.application.interfaces import (
    IAssetRepository,
    IMachineRepository,
    IProductionLineRepository,
    ITelemetryPointRepository,
)
from industrial_oracle.assets.domain.models import Asset, Machine, ProductionLine, TelemetryPoint


class InMemoryAssetRepository(IAssetRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, Asset] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Asset]:
        return self._storage.get(entity_id)

    async def get_by_tag(self, organization_id: uuid.UUID, asset_tag: str) -> Optional[Asset]:
        return next(
            (a for a in self._storage.values() if a.organization_id == organization_id and a.asset_tag == asset_tag),
            None,
        )

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Asset]:
        assets = [a for a in self._storage.values() if a.organization_id == organization_id]
        if plant_id:
            assets = [a for a in assets if a.plant_id == plant_id]
        if status:
            assets = [a for a in assets if a.status == status]
        assets.sort(key=lambda x: x.created_at, reverse=True)
        return assets[offset : offset + limit]

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[Asset]:
        return await self.list_by_organization(organization_id, offset=offset, limit=limit)

    async def add(self, entity: Asset) -> Asset:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: Asset) -> Asset:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


class InMemoryProductionLineRepository(IProductionLineRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, ProductionLine] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ProductionLine]:
        return self._storage.get(entity_id)

    async def get_by_code(self, plant_id: uuid.UUID, code: str) -> Optional[ProductionLine]:
        return next(
            (pl for pl in self._storage.values() if pl.plant_id == plant_id and pl.code == code),
            None,
        )

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ProductionLine]:
        lines = [pl for pl in self._storage.values() if pl.organization_id == organization_id]
        if plant_id:
            lines = [pl for pl in lines if pl.plant_id == plant_id]
        lines.sort(key=lambda x: x.created_at, reverse=True)
        return lines[offset : offset + limit]

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[ProductionLine]:
        return await self.list_by_organization(organization_id, offset=offset, limit=limit)

    async def add(self, entity: ProductionLine) -> ProductionLine:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: ProductionLine) -> ProductionLine:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


class InMemoryMachineRepository(IMachineRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, Machine] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[Machine]:
        return self._storage.get(entity_id)

    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        production_line_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Machine]:
        machines = [m for m in self._storage.values() if m.organization_id == organization_id]
        if production_line_id:
            machines = [m for m in machines if m.production_line_id == production_line_id]
        if status:
            machines = [m for m in machines if m.status == status]
        machines.sort(key=lambda x: x.created_at, reverse=True)
        return machines[offset : offset + limit]

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[Machine]:
        return await self.list_by_organization(organization_id, offset=offset, limit=limit)

    async def add(self, entity: Machine) -> Machine:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: Machine) -> Machine:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


class InMemoryTelemetryPointRepository(ITelemetryPointRepository):
    def __init__(self) -> None:
        self._storage: Dict[uuid.UUID, TelemetryPoint] = {}

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[TelemetryPoint]:
        return self._storage.get(entity_id)

    async def list_by_machine(self, machine_id: uuid.UUID) -> List[TelemetryPoint]:
        return [tp for tp in self._storage.values() if tp.machine_id == machine_id]

    async def list(self, organization_id: uuid.UUID, offset: int = 0, limit: int = 50, filters: Optional[dict] = None) -> List[TelemetryPoint]:
        return [tp for tp in self._storage.values() if tp.organization_id == organization_id][offset : offset + limit]

    async def add(self, entity: TelemetryPoint) -> TelemetryPoint:
        self._storage[entity.id] = entity
        return entity

    async def update(self, entity: TelemetryPoint) -> TelemetryPoint:
        self._storage[entity.id] = entity
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        return self._storage.pop(entity_id, None) is not None


asset_repo = InMemoryAssetRepository()
production_line_repo = InMemoryProductionLineRepository()
machine_repo = InMemoryMachineRepository()
telemetry_point_repo = InMemoryTelemetryPointRepository()
