"""Asset, Production Line, Machine, and Telemetry repository interfaces."""

from abc import abstractmethod
from typing import List, Optional
import uuid

from industrial_oracle.assets.domain.models import Asset, Machine, ProductionLine, TelemetryPoint
from industrial_oracle.shared.application.repository import GenericRepository


class IAssetRepository(GenericRepository[Asset, uuid.UUID]):
    @abstractmethod
    async def get_by_tag(self, organization_id: uuid.UUID, asset_tag: str) -> Optional[Asset]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Asset]:
        raise NotImplementedError


class IProductionLineRepository(GenericRepository[ProductionLine, uuid.UUID]):
    @abstractmethod
    async def get_by_code(self, plant_id: uuid.UUID, code: str) -> Optional[ProductionLine]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ProductionLine]:
        raise NotImplementedError


class IMachineRepository(GenericRepository[Machine, uuid.UUID]):
    @abstractmethod
    async def list_by_organization(
        self,
        organization_id: uuid.UUID,
        production_line_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[Machine]:
        raise NotImplementedError


class ITelemetryPointRepository(GenericRepository[TelemetryPoint, uuid.UUID]):
    @abstractmethod
    async def list_by_machine(self, machine_id: uuid.UUID) -> List[TelemetryPoint]:
        raise NotImplementedError
