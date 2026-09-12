"""Asset, Production Line, Machine, and Telemetry application services."""

from typing import List, Optional
import uuid

from industrial_oracle.assets.application.dtos import (
    AssetCreateDTO,
    AssetResponseDTO,
    AssetUpdateDTO,
    MachineCreateDTO,
    MachineFaultDTO,
    MachineResponseDTO,
    MachineUpdateDTO,
    ProductionLineCreateDTO,
    ProductionLineResponseDTO,
    TelemetryPointCreateDTO,
    TelemetryPointResponseDTO,
)
from industrial_oracle.assets.application.interfaces import (
    IAssetRepository,
    IMachineRepository,
    IProductionLineRepository,
    ITelemetryPointRepository,
)
from industrial_oracle.assets.domain.models import (
    Asset,
    AssetStatus,
    Machine,
    ProductionLine,
    TelemetryPoint,
)
from industrial_oracle.audit.application.service import audit_service
from industrial_oracle.core.exceptions import (
    BusinessRuleViolationException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
    ValidationException,
)
from industrial_oracle.organization.application.interfaces import IPlantRepository
from industrial_oracle.shared.infrastructure.event_bus import event_bus


class AssetService:
    def __init__(
        self,
        asset_repo: IAssetRepository,
        plant_repo: IPlantRepository,
    ) -> None:
        self.asset_repo = asset_repo
        self.plant_repo = plant_repo

    async def create_asset(
        self,
        dto: AssetCreateDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> AssetResponseDTO:
        # Validate unique asset_tag in this organization
        existing = await self.asset_repo.get_by_tag(organization_id, dto.asset_tag)
        if existing:
            raise EntityAlreadyExistsException("Asset", "asset_tag", dto.asset_tag)

        # Validate plant belongs to organization if specified
        if dto.plant_id:
            plant = await self.plant_repo.get_by_id(dto.plant_id)
            if not plant or plant.organization_id != organization_id:
                raise EntityNotFoundException("Plant", dto.plant_id)

        asset = Asset(
            organization_id=organization_id,
            plant_id=dto.plant_id,
            name=dto.name,
            asset_tag=dto.asset_tag,
            asset_type=dto.asset_type,
            serial_number=dto.serial_number,
            critical=dto.critical,
            location_in_plant=dto.location_in_plant,
        )
        await self.asset_repo.add(asset)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="ASSET_CREATED",
            resource_type="Asset",
            resource_id=str(asset.id),
            new_value={"name": asset.name, "tag": asset.asset_tag, "type": asset.asset_type},
        )

        return AssetResponseDTO.model_validate(asset)

    async def get_asset(self, asset_id: uuid.UUID, organization_id: uuid.UUID) -> AssetResponseDTO:
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset or asset.organization_id != organization_id:
            raise EntityNotFoundException("Asset", asset_id)
        return AssetResponseDTO.model_validate(asset)

    async def list_assets(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[AssetResponseDTO]:
        assets = await self.asset_repo.list_by_organization(
            organization_id=organization_id,
            plant_id=plant_id,
            status=status,
            offset=offset,
            limit=limit,
        )
        return [AssetResponseDTO.model_validate(a) for a in assets]

    async def update_asset(
        self,
        asset_id: uuid.UUID,
        dto: AssetUpdateDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> AssetResponseDTO:
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset or asset.organization_id != organization_id:
            raise EntityNotFoundException("Asset", asset_id)

        old_state = {"name": asset.name, "plant_id": str(asset.plant_id) if asset.plant_id else None}

        if dto.plant_id is not None:
            plant = await self.plant_repo.get_by_id(dto.plant_id)
            if not plant or plant.organization_id != organization_id:
                raise EntityNotFoundException("Plant", dto.plant_id)
            asset.plant_id = dto.plant_id

        if dto.name is not None:
            asset.name = dto.name
        if dto.asset_type is not None:
            asset.asset_type = dto.asset_type
        if dto.serial_number is not None:
            asset.serial_number = dto.serial_number
        if dto.critical is not None:
            asset.critical = dto.critical
        if dto.location_in_plant is not None:
            asset.location_in_plant = dto.location_in_plant

        await self.asset_repo.update(asset)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="ASSET_UPDATED",
            resource_type="Asset",
            resource_id=str(asset.id),
            old_value=old_state,
            new_value={"name": asset.name, "plant_id": str(asset.plant_id) if asset.plant_id else None},
        )

        return AssetResponseDTO.model_validate(asset)

    async def change_asset_status(
        self,
        asset_id: uuid.UUID,
        new_status: str,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> AssetResponseDTO:
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset or asset.organization_id != organization_id:
            raise EntityNotFoundException("Asset", asset_id)

        old_status = asset.status
        if new_status == AssetStatus.IN_SERVICE.value:
            asset.return_to_service()
        elif new_status == AssetStatus.MAINTENANCE.value:
            asset.send_to_maintenance()
        elif new_status == AssetStatus.OUT_OF_SERVICE.value:
            asset.take_out_of_service()
        elif new_status == AssetStatus.DECOMMISSIONED.value:
            asset.decommission()
        else:
            raise ValidationException(f"Invalid asset status: {new_status}")

        await self.asset_repo.update(asset)
        await event_bus.publish_all(asset.collect_events())

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="ASSET_STATUS_CHANGED",
            resource_type="Asset",
            resource_id=str(asset.id),
            old_value={"status": old_status},
            new_value={"status": asset.status},
        )

        return AssetResponseDTO.model_validate(asset)

    async def delete_asset(
        self,
        asset_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> bool:
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset or asset.organization_id != organization_id:
            raise EntityNotFoundException("Asset", asset_id)

        success = await self.asset_repo.delete(asset_id)
        if success:
            await audit_service.record_action(
                organization_id=organization_id,
                actor_id=actor_id,
                action="ASSET_DELETED",
                resource_type="Asset",
                resource_id=str(asset_id),
            )
        return success


class ProductionLineService:
    def __init__(
        self,
        line_repo: IProductionLineRepository,
        plant_repo: IPlantRepository,
    ) -> None:
        self.line_repo = line_repo
        self.plant_repo = plant_repo

    async def create_production_line(
        self,
        dto: ProductionLineCreateDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> ProductionLineResponseDTO:
        # Validate plant belongs to organization
        plant = await self.plant_repo.get_by_id(dto.plant_id)
        if not plant or plant.organization_id != organization_id:
            raise EntityNotFoundException("Plant", dto.plant_id)

        # Unique line code per plant
        existing = await self.line_repo.get_by_code(dto.plant_id, dto.code)
        if existing:
            raise EntityAlreadyExistsException("ProductionLine", "code", dto.code)

        line = ProductionLine(
            organization_id=organization_id,
            plant_id=dto.plant_id,
            name=dto.name,
            code=dto.code,
            capacity_units_per_hour=dto.capacity_units_per_hour,
        )
        await self.line_repo.add(line)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="PRODUCTION_LINE_CREATED",
            resource_type="ProductionLine",
            resource_id=str(line.id),
            new_value={"name": line.name, "code": line.code, "capacity": line.capacity_units_per_hour},
        )

        return ProductionLineResponseDTO.model_validate(line)

    async def get_production_line(self, line_id: uuid.UUID, organization_id: uuid.UUID) -> ProductionLineResponseDTO:
        line = await self.line_repo.get_by_id(line_id)
        if not line or line.organization_id != organization_id:
            raise EntityNotFoundException("ProductionLine", line_id)
        return ProductionLineResponseDTO.model_validate(line)

    async def list_production_lines(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[ProductionLineResponseDTO]:
        lines = await self.line_repo.list_by_organization(
            organization_id=organization_id,
            plant_id=plant_id,
            offset=offset,
            limit=limit,
        )
        return [ProductionLineResponseDTO.model_validate(l) for l in lines]


class MachineService:
    def __init__(
        self,
        machine_repo: IMachineRepository,
        asset_repo: IAssetRepository,
        line_repo: IProductionLineRepository,
    ) -> None:
        self.machine_repo = machine_repo
        self.asset_repo = asset_repo
        self.line_repo = line_repo

    async def create_machine(
        self,
        dto: MachineCreateDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> MachineResponseDTO:
        # Validate asset belongs to this tenant organization
        asset = await self.asset_repo.get_by_id(dto.asset_id)
        if not asset or asset.organization_id != organization_id:
            raise EntityNotFoundException("Asset", dto.asset_id)

        # Validate line if specified
        if dto.production_line_id:
            line = await self.line_repo.get_by_id(dto.production_line_id)
            if not line or line.organization_id != organization_id:
                raise EntityNotFoundException("ProductionLine", dto.production_line_id)

        machine = Machine(
            organization_id=organization_id,
            asset_id=dto.asset_id,
            name=dto.name,
            production_line_id=dto.production_line_id,
            model=dto.model,
            power_rating_kw=dto.power_rating_kw,
            operating_hours=dto.operating_hours,
        )
        await self.machine_repo.add(machine)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="MACHINE_CREATED",
            resource_type="Machine",
            resource_id=str(machine.id),
            new_value={"name": machine.name, "power_kw": machine.power_rating_kw},
        )

        return MachineResponseDTO.model_validate(machine)

    async def get_machine(self, machine_id: uuid.UUID, organization_id: uuid.UUID) -> MachineResponseDTO:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)
        return MachineResponseDTO.model_validate(machine)

    async def list_machines(
        self,
        organization_id: uuid.UUID,
        production_line_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> List[MachineResponseDTO]:
        machines = await self.machine_repo.list_by_organization(
            organization_id=organization_id,
            production_line_id=production_line_id,
            status=status,
            offset=offset,
            limit=limit,
        )
        return [MachineResponseDTO.model_validate(m) for m in machines]

    async def start_machine(
        self,
        machine_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> MachineResponseDTO:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)

        machine.start()
        await self.machine_repo.update(machine)
        await event_bus.publish_all(machine.collect_events())

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="MACHINE_STARTED",
            resource_type="Machine",
            resource_id=str(machine.id),
        )

        return MachineResponseDTO.model_validate(machine)

    async def stop_machine(
        self,
        machine_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> MachineResponseDTO:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)

        machine.stop()
        await self.machine_repo.update(machine)
        await event_bus.publish_all(machine.collect_events())

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="MACHINE_STOPPED",
            resource_type="Machine",
            resource_id=str(machine.id),
        )

        return MachineResponseDTO.model_validate(machine)

    async def record_machine_fault(
        self,
        machine_id: uuid.UUID,
        dto: MachineFaultDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> MachineResponseDTO:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)

        machine.record_fault(dto.fault_code, dto.description)
        await self.machine_repo.update(machine)
        await event_bus.publish_all(machine.collect_events())

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="MACHINE_FAULT_RECORDED",
            resource_type="Machine",
            resource_id=str(machine.id),
            new_value={"code": dto.fault_code, "desc": dto.description},
        )

        return MachineResponseDTO.model_validate(machine)

    async def clear_machine_fault(
        self,
        machine_id: uuid.UUID,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> MachineResponseDTO:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)

        machine.clear_fault()
        await self.machine_repo.update(machine)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="MACHINE_FAULT_CLEARED",
            resource_type="Machine",
            resource_id=str(machine.id),
        )

        return MachineResponseDTO.model_validate(machine)

    async def log_operating_hours(
        self,
        machine_id: uuid.UUID,
        hours: float,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> MachineResponseDTO:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)

        machine.log_operating_hours(hours)
        await self.machine_repo.update(machine)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="MACHINE_HOURS_LOGGED",
            resource_type="Machine",
            resource_id=str(machine.id),
            new_value={"added_hours": hours, "total_hours": machine.operating_hours},
        )

        return MachineResponseDTO.model_validate(machine)


class TelemetryService:
    def __init__(
        self,
        telemetry_repo: ITelemetryPointRepository,
        machine_repo: IMachineRepository,
    ) -> None:
        self.telemetry_repo = telemetry_repo
        self.machine_repo = machine_repo

    async def bind_telemetry_point(
        self,
        machine_id: uuid.UUID,
        dto: TelemetryPointCreateDTO,
        organization_id: uuid.UUID,
        actor_id: uuid.UUID,
    ) -> TelemetryPointResponseDTO:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)

        point = TelemetryPoint(
            organization_id=organization_id,
            machine_id=machine_id,
            metric_name=dto.metric_name,
            unit=dto.unit,
            min_threshold=dto.min_threshold,
            max_threshold=dto.max_threshold,
        )
        await self.telemetry_repo.add(point)

        await audit_service.record_action(
            organization_id=organization_id,
            actor_id=actor_id,
            action="TELEMETRY_POINT_BOUND",
            resource_type="TelemetryPoint",
            resource_id=str(point.id),
            new_value={"metric": point.metric_name, "unit": point.unit},
        )

        return TelemetryPointResponseDTO.model_validate(point)

    async def list_machine_telemetry(
        self,
        machine_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> List[TelemetryPointResponseDTO]:
        machine = await self.machine_repo.get_by_id(machine_id)
        if not machine or machine.organization_id != organization_id:
            raise EntityNotFoundException("Machine", machine_id)

        points = await self.telemetry_repo.list_by_machine(machine_id)
        return [TelemetryPointResponseDTO.model_validate(p) for p in points]
