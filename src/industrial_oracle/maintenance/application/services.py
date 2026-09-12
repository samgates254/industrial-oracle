"""Maintenance application service coordinating asset/machine state and parts consumption."""

from datetime import datetime, timezone
from typing import Any, List, Optional
import uuid

from industrial_oracle.assets.infrastructure.repository import asset_repo, machine_repo
from industrial_oracle.audit.application.service import audit_service
from industrial_oracle.core.exceptions import (
    BusinessRuleViolationException,
    EntityNotFoundException,
)
from industrial_oracle.inventory.application.services import inventory_service
from industrial_oracle.maintenance.application.dtos import (
    MaintenanceCompleteDTO,
    MaintenanceOrderCreateDTO,
    MaintenanceOrderResponseDTO,
    MaintenanceOrderUpdateDTO,
)
from industrial_oracle.maintenance.application.interfaces import IMaintenanceOrderRepository
from industrial_oracle.maintenance.domain.maintenance_order import MaintenanceStatus, MaintenanceWorkOrder
from industrial_oracle.maintenance.infrastructure.repository import maintenance_order_repo
from industrial_oracle.operations.application.dtos import MaterialConsumeDTO, MaterialConsumptionResponseDTO, WorkOrderCreateDTO
from industrial_oracle.operations.application.services import work_order_service
from industrial_oracle.operations.domain.consumption import ConsumerType, MaterialConsumption
from industrial_oracle.operations.domain.work_order import WorkOrder, WorkOrderStatus, WorkOrderType
from industrial_oracle.operations.infrastructure.repository import material_consumption_repo, work_order_repo
from industrial_oracle.shared.domain.events import DomainEvent
from industrial_oracle.shared.infrastructure.event_bus import event_bus
from industrial_oracle.integrations.infrastructure.repository import outbox_repository


class MaintenanceService:
    def __init__(
        self,
        repository: IMaintenanceOrderRepository = maintenance_order_repo,
        outbox_repo = None,
    ) -> None:
        self._repo = repository
        self._outbox_repo = outbox_repo or outbox_repository

    async def _emit(self, ev: DomainEvent, session: Optional[Any] = None) -> None:
        # Synchronous request path offloads event dispatch to durable outbox worker
        await self._outbox_repo.append_domain_event(ev, session=session)

    async def create_maintenance_order(
        self, organization_id: uuid.UUID, dto: MaintenanceOrderCreateDTO, actor_id: uuid.UUID
    ) -> MaintenanceOrderResponseDTO:
        if not dto.asset_id and not dto.machine_id:
            raise BusinessRuleViolationException(
                "Maintenance work order requires at least an Asset or Machine ID.",
                rule_name="MISSING_EQUIPMENT_REFERENCE",
            )

        if dto.asset_id:
            asset = await asset_repo.get_by_id(dto.asset_id)
            if not asset or asset.organization_id != organization_id:
                raise EntityNotFoundException("Asset not found in this organization.")

        if dto.machine_id:
            machine = await machine_repo.get_by_id(dto.machine_id)
            if not machine or machine.organization_id != organization_id:
                raise EntityNotFoundException("Machine not found in this organization.")

        # Create the underlying authorized Work Order in DRAFT status
        wo_dto = WorkOrderCreateDTO(
            site_id=dto.site_id,
            plant_id=dto.plant_id,
            work_order_number=dto.work_order_number,
            title=dto.title,
            description=dto.fault_description,
            work_order_type=WorkOrderType.MAINTENANCE.value,
            priority=dto.priority,
            machine_id=dto.machine_id,
            asset_id=dto.asset_id,
            planned_start=dto.planned_start,
            planned_end=dto.planned_end,
            assigned_to=dto.technician_id,
        )
        wo_response = await work_order_service.create_work_order(
            organization_id=organization_id, dto=wo_dto, actor_id=actor_id
        )

        maint_order = MaintenanceWorkOrder(
            organization_id=organization_id,
            work_order_id=wo_response.id,
            maintenance_type=dto.maintenance_type,
            fault_description=dto.fault_description,
            asset_id=dto.asset_id,
            machine_id=dto.machine_id,
            status=MaintenanceStatus.PLANNED.value,
            failure_code=dto.failure_code,
            technician_id=dto.technician_id,
        )
        saved = await self._repo.add(maint_order)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="MAINTENANCE_WORK_ORDER_CREATED",
            resource_type="MaintenanceWorkOrder",
            resource_id=saved.id,
            metadata={
                "work_order_id": str(saved.work_order_id),
                "maintenance_type": saved.maintenance_type,
                "asset_id": str(saved.asset_id) if saved.asset_id else None,
                "machine_id": str(saved.machine_id) if saved.machine_id else None,
            },
        )
        return await self._to_dto(saved)

    async def get_maintenance_order(
        self, organization_id: uuid.UUID, maintenance_id: uuid.UUID
    ) -> MaintenanceOrderResponseDTO:
        order = await self._repo.get_by_id(maintenance_id)
        if not order or order.organization_id != organization_id:
            raise EntityNotFoundException("Maintenance work order not found in this organization.")
        return await self._to_dto(order)

    async def list_maintenance_orders(
        self,
        organization_id: uuid.UUID,
        asset_id: Optional[uuid.UUID] = None,
        machine_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[MaintenanceOrderResponseDTO]:
        orders = await self._repo.list_by_organization(
            organization_id, asset_id=asset_id, machine_id=machine_id, status=status, limit=limit, offset=offset
        )
        dtos = []
        for o in orders:
            dtos.append(await self._to_dto(o))
        return dtos

    async def start_maintenance(
        self, organization_id: uuid.UUID, maintenance_id: uuid.UUID, actor_id: uuid.UUID
    ) -> MaintenanceOrderResponseDTO:
        order = await self._repo.get_by_id(maintenance_id)
        if not order or order.organization_id != organization_id:
            raise EntityNotFoundException("Maintenance work order not found in this organization.")

        # Coordinate Machine State Machine: transition machine to MAINTENANCE state
        if order.machine_id:
            machine = await machine_repo.get_by_id(order.machine_id)
            if machine and machine.organization_id == organization_id:
                machine.set_maintenance()
                await machine_repo.update(machine)
                for ev in machine.collect_events():
                    await self._emit(ev)

        # Coordinate Asset State Machine: send asset to maintenance if present
        if order.asset_id:
            asset = await asset_repo.get_by_id(order.asset_id)
            if asset and asset.organization_id == organization_id and asset.status != "MAINTENANCE":
                asset.send_to_maintenance()
                await asset_repo.update(asset)
                for ev in asset.collect_events():
                    await self._emit(ev)

        # Also release and start underlying Work Order if in DRAFT/RELEASED
        wo = await work_order_repo.get_by_id(order.work_order_id)
        if wo and wo.organization_id == organization_id:
            if wo.status == WorkOrderStatus.DRAFT.value:
                wo.release()
            if wo.status in (WorkOrderStatus.RELEASED.value, WorkOrderStatus.ON_HOLD.value):
                wo.start()
            await work_order_repo.update(wo)
            for ev in wo.collect_events():
                await self._emit(ev)

        order.start()
        updated = await self._repo.update(order)
        for event in order.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="MAINTENANCE_STARTED",
            resource_type="MaintenanceWorkOrder",
            resource_id=updated.id,
            metadata={"work_order_id": str(updated.work_order_id)},
        )
        return await self._to_dto(updated)

    async def complete_maintenance(
        self,
        organization_id: uuid.UUID,
        maintenance_id: uuid.UUID,
        dto: MaintenanceCompleteDTO,
        actor_id: uuid.UUID,
    ) -> MaintenanceOrderResponseDTO:
        order = await self._repo.get_by_id(maintenance_id)
        if not order or order.organization_id != organization_id:
            raise EntityNotFoundException("Maintenance work order not found in this organization.")

        # Coordinate Machine State Machine: restore machine from MAINTENANCE to STOPPED
        if order.machine_id:
            machine = await machine_repo.get_by_id(order.machine_id)
            if machine and machine.organization_id == organization_id:
                if machine.status == "MAINTENANCE":
                    machine.complete_maintenance()
                    await machine_repo.update(machine)
                    for ev in machine.collect_events():
                        await self._emit(ev)

        # Coordinate Asset State Machine: return asset to service if in MAINTENANCE
        if order.asset_id:
            asset = await asset_repo.get_by_id(order.asset_id)
            if asset and asset.organization_id == organization_id and asset.status == "MAINTENANCE":
                asset.return_to_service()
                await asset_repo.update(asset)
                for ev in asset.collect_events():
                    await self._emit(ev)

        # Complete underlying Work Order
        wo = await work_order_repo.get_by_id(order.work_order_id)
        if wo and wo.organization_id == organization_id:
            if wo.status == WorkOrderStatus.IN_PROGRESS.value:
                wo.complete()
                await work_order_repo.update(wo)
                for ev in wo.collect_events():
                    await self._emit(ev)

        order.complete(
            corrective_action=dto.corrective_action,
            root_cause=dto.root_cause,
            downtime_minutes=dto.downtime_minutes,
        )
        updated = await self._repo.update(order)
        for event in order.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="MAINTENANCE_COMPLETED",
            resource_type="MaintenanceWorkOrder",
            resource_id=updated.id,
            metadata={"work_order_id": str(updated.work_order_id), "downtime_minutes": updated.downtime_minutes},
        )
        return await self._to_dto(updated)

    async def consume_material(
        self,
        organization_id: uuid.UUID,
        maintenance_id: uuid.UUID,
        dto: MaterialConsumeDTO,
        actor_id: uuid.UUID,
    ) -> MaterialConsumptionResponseDTO:
        order = await self._repo.get_by_id(maintenance_id)
        if not order or order.organization_id != organization_id:
            raise EntityNotFoundException("Maintenance work order not found in this organization.")

        tx = await inventory_service.consume_material(
            organization_id=organization_id,
            consumer_type=ConsumerType.MAINTENANCE_WORK_ORDER.value,
            consumer_id=order.id,
            item_id=dto.item_id,
            location_id=dto.location_id,
            quantity=dto.quantity,
            actor_id=actor_id,
        )

        consumption = MaterialConsumption(
            organization_id=organization_id,
            consumer_type=ConsumerType.MAINTENANCE_WORK_ORDER.value,
            consumer_id=order.id,
            item_id=dto.item_id,
            location_id=dto.location_id,
            quantity=dto.quantity,
            inventory_transaction_id=tx.id,
            consumed_by=actor_id,
        )
        saved = await material_consumption_repo.add(consumption)

        await self._emit(
            DomainEvent(
                event_type="MaterialConsumed",
                aggregate_id=str(saved.id),
                aggregate_type="MaterialConsumption",
                organization_id=str(organization_id),
                payload={
                    "consumer_type": saved.consumer_type,
                    "consumer_id": str(saved.consumer_id),
                    "item_id": str(saved.item_id),
                    "quantity": saved.quantity,
                },
            )
        )

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="MATERIAL_CONSUMED",
            resource_type="MaterialConsumption",
            resource_id=saved.id,
            metadata={
                "consumer_type": saved.consumer_type,
                "consumer_id": str(saved.consumer_id),
                "item_id": str(saved.item_id),
                "quantity": saved.quantity,
            },
        )

        return MaterialConsumptionResponseDTO(
            id=saved.id,
            organization_id=saved.organization_id,
            consumer_type=saved.consumer_type,
            consumer_id=saved.consumer_id,
            item_id=saved.item_id,
            location_id=saved.location_id,
            quantity=saved.quantity,
            inventory_transaction_id=saved.inventory_transaction_id,
            consumed_by=saved.consumed_by,
            consumed_at=saved.consumed_at,
        )

    async def _to_dto(self, order: MaintenanceWorkOrder) -> MaintenanceOrderResponseDTO:
        wo = await work_order_repo.get_by_id(order.work_order_id)
        wo_number = wo.work_order_number if wo else "UNKNOWN"
        wo_title = wo.title if wo else "Maintenance Order"
        wo_priority = wo.priority if wo else "HIGH"

        return MaintenanceOrderResponseDTO(
            id=order.id,
            organization_id=order.organization_id,
            work_order_id=order.work_order_id,
            work_order_number=wo_number,
            title=wo_title,
            maintenance_type=order.maintenance_type,
            status=order.status,
            priority=wo_priority,
            fault_description=order.fault_description,
            asset_id=order.asset_id,
            machine_id=order.machine_id,
            failure_code=order.failure_code,
            root_cause=order.root_cause,
            corrective_action=order.corrective_action,
            technician_id=order.technician_id,
            downtime_minutes=order.downtime_minutes,
            maintenance_started_at=order.maintenance_started_at,
            maintenance_completed_at=order.maintenance_completed_at,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )


# Singleton service instance
maintenance_service = MaintenanceService()
