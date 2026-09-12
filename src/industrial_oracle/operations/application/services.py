"""Application services for Operations (Work Orders, Production Runs, and Material Consumption)."""

from datetime import datetime, timezone
from typing import Any, List, Optional
import uuid

from industrial_oracle.assets.infrastructure.repository import asset_repo, machine_repo, production_line_repo
from industrial_oracle.audit.application.service import audit_service
from industrial_oracle.core.exceptions import (
    BusinessRuleViolationException,
    EntityAlreadyExistsException,
    EntityNotFoundException,
)
from industrial_oracle.inventory.application.services import inventory_service
from industrial_oracle.operations.application.dtos import (
    MaterialConsumeDTO,
    MaterialConsumptionResponseDTO,
    ProductionQuantityRecordDTO,
    ProductionRunCreateDTO,
    ProductionRunResponseDTO,
    WorkOrderCreateDTO,
    WorkOrderResponseDTO,
    WorkOrderUpdateDTO,
)
from industrial_oracle.operations.application.interfaces import (
    IMaterialConsumptionRepository,
    IProductionRunRepository,
    IWorkOrderRepository,
)
from industrial_oracle.operations.domain.consumption import ConsumerType, MaterialConsumption
from industrial_oracle.operations.domain.production_run import ProductionRun
from industrial_oracle.operations.domain.work_order import WorkOrder, WorkOrderStatus
from industrial_oracle.operations.infrastructure.repository import (
    material_consumption_repo,
    production_run_repo,
    work_order_repo,
)
from industrial_oracle.organization.infrastructure.repository import plant_repo, site_repo
from industrial_oracle.shared.domain.events import DomainEvent
from industrial_oracle.shared.infrastructure.event_bus import event_bus
from industrial_oracle.integrations.infrastructure.repository import outbox_repository


class WorkOrderService:
    def __init__(self, repository: IWorkOrderRepository = work_order_repo, outbox_repo = None) -> None:
        self._repo = repository
        self._outbox_repo = outbox_repo or outbox_repository

    async def _emit(self, ev: DomainEvent, session: Optional[Any] = None) -> None:
        # Synchronous request path offloads event dispatch to durable outbox worker
        await self._outbox_repo.append_domain_event(ev, session=session)

    async def create_work_order(
        self, organization_id: uuid.UUID, dto: WorkOrderCreateDTO, actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        site = await site_repo.get_by_id(dto.site_id)
        if not site or site.organization_id != organization_id:
            raise EntityNotFoundException("Site not found in this organization.")

        plant = await plant_repo.get_by_id(dto.plant_id)
        if not plant or plant.organization_id != organization_id:
            raise EntityNotFoundException("Plant not found in this organization.")

        if dto.production_line_id:
            line = await production_line_repo.get_by_id(dto.production_line_id)
            if not line or line.organization_id != organization_id:
                raise EntityNotFoundException("Production line not found in this organization.")

        if dto.machine_id:
            machine = await machine_repo.get_by_id(dto.machine_id)
            if not machine or machine.organization_id != organization_id:
                raise EntityNotFoundException("Machine not found in this organization.")

        if dto.asset_id:
            asset = await asset_repo.get_by_id(dto.asset_id)
            if not asset or asset.organization_id != organization_id:
                raise EntityNotFoundException("Asset not found in this organization.")

        existing = await self._repo.get_by_number(organization_id, dto.work_order_number)
        if existing:
            raise EntityAlreadyExistsException(
                f"Work order with number '{dto.work_order_number}' already exists in organization."
            )

        wo = WorkOrder(
            organization_id=organization_id,
            site_id=dto.site_id,
            plant_id=dto.plant_id,
            production_line_id=dto.production_line_id,
            machine_id=dto.machine_id,
            asset_id=dto.asset_id,
            work_order_number=dto.work_order_number,
            title=dto.title,
            description=dto.description,
            work_order_type=dto.work_order_type,
            priority=dto.priority,
            status=WorkOrderStatus.DRAFT.value,
            planned_start=dto.planned_start,
            planned_end=dto.planned_end,
            created_by=actor_id,
            assigned_to=dto.assigned_to,
        )
        saved = await self._repo.add(wo)

        await self._emit(
            DomainEvent(
                event_type="WorkOrderCreated",
                aggregate_id=str(saved.id),
                aggregate_type="WorkOrder",
                organization_id=str(organization_id),
                payload={"work_order_number": saved.work_order_number, "type": saved.work_order_type},
            )
        )

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_CREATED",
            resource_type="WorkOrder",
            resource_id=saved.id,
            metadata={"work_order_number": saved.work_order_number, "title": saved.title},
        )
        return self._to_dto(saved)

    async def get_work_order(self, organization_id: uuid.UUID, work_order_id: uuid.UUID) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")
        return self._to_dto(wo)

    async def list_work_orders(
        self,
        organization_id: uuid.UUID,
        plant_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        work_order_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WorkOrderResponseDTO]:
        orders = await self._repo.list_by_organization(
            organization_id, plant_id=plant_id, status=status, work_order_type=work_order_type, limit=limit, offset=offset
        )
        return [self._to_dto(w) for w in orders]

    async def update_work_order(
        self, organization_id: uuid.UUID, work_order_id: uuid.UUID, dto: WorkOrderUpdateDTO, actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")
        if wo.status in (WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value):
            raise BusinessRuleViolationException("Cannot update completed or cancelled work order.")

        if dto.title is not None:
            wo.title = dto.title.strip()
        if dto.description is not None:
            wo.description = dto.description
        if dto.priority is not None:
            wo.priority = dto.priority
        if dto.planned_start is not None:
            wo.planned_start = dto.planned_start
        if dto.planned_end is not None:
            wo.planned_end = dto.planned_end
        if dto.assigned_to is not None:
            wo.assigned_to = dto.assigned_to
        wo.version += 1
        wo.updated_at = datetime.now(timezone.utc)

        updated = await self._repo.update(wo)
        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_UPDATED",
            resource_type="WorkOrder",
            resource_id=updated.id,
            metadata={"work_order_number": updated.work_order_number},
        )
        return self._to_dto(updated)

    async def release_work_order(
        self, organization_id: uuid.UUID, work_order_id: uuid.UUID, actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")

        wo.release()
        updated = await self._repo.update(wo)
        for event in wo.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_RELEASED",
            resource_type="WorkOrder",
            resource_id=updated.id,
            metadata={"work_order_number": updated.work_order_number},
        )
        return self._to_dto(updated)

    async def start_work_order(
        self, organization_id: uuid.UUID, work_order_id: uuid.UUID, actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")

        wo.start()
        updated = await self._repo.update(wo)
        for event in wo.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_STARTED",
            resource_type="WorkOrder",
            resource_id=updated.id,
            metadata={"work_order_number": updated.work_order_number},
        )
        return self._to_dto(updated)

    async def hold_work_order(
        self, organization_id: uuid.UUID, work_order_id: uuid.UUID, reason: Optional[str], actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")

        wo.put_on_hold(reason)
        updated = await self._repo.update(wo)
        for event in wo.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_HOLD",
            resource_type="WorkOrder",
            resource_id=updated.id,
            metadata={"work_order_number": updated.work_order_number, "reason": reason},
        )
        return self._to_dto(updated)

    async def resume_work_order(
        self, organization_id: uuid.UUID, work_order_id: uuid.UUID, actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")

        wo.resume()
        updated = await self._repo.update(wo)
        for event in wo.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_RESUMED",
            resource_type="WorkOrder",
            resource_id=updated.id,
            metadata={"work_order_number": updated.work_order_number},
        )
        return self._to_dto(updated)

    async def complete_work_order(
        self, organization_id: uuid.UUID, work_order_id: uuid.UUID, actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")

        wo.complete()
        updated = await self._repo.update(wo)
        for event in wo.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_COMPLETED",
            resource_type="WorkOrder",
            resource_id=updated.id,
            metadata={"work_order_number": updated.work_order_number},
        )
        return self._to_dto(updated)

    async def cancel_work_order(
        self, organization_id: uuid.UUID, work_order_id: uuid.UUID, reason: Optional[str], actor_id: uuid.UUID
    ) -> WorkOrderResponseDTO:
        wo = await self._repo.get_by_id(work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Work order not found in this organization.")

        wo.cancel(reason)
        updated = await self._repo.update(wo)
        for event in wo.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="WORK_ORDER_CANCELLED",
            resource_type="WorkOrder",
            resource_id=updated.id,
            metadata={"work_order_number": updated.work_order_number, "reason": reason},
        )
        return self._to_dto(updated)

    def _to_dto(self, wo: WorkOrder) -> WorkOrderResponseDTO:
        return WorkOrderResponseDTO(
            id=wo.id,
            organization_id=wo.organization_id,
            site_id=wo.site_id,
            plant_id=wo.plant_id,
            production_line_id=wo.production_line_id,
            machine_id=wo.machine_id,
            asset_id=wo.asset_id,
            work_order_number=wo.work_order_number,
            title=wo.title,
            description=wo.description,
            work_order_type=wo.work_order_type,
            priority=wo.priority,
            status=wo.status,
            planned_start=wo.planned_start,
            planned_end=wo.planned_end,
            actual_start=wo.actual_start,
            actual_end=wo.actual_end,
            created_by=wo.created_by,
            assigned_to=wo.assigned_to,
            version=wo.version,
            created_at=wo.created_at,
            updated_at=wo.updated_at,
        )


class ProductionRunService:
    def __init__(
        self,
        repository: IProductionRunRepository = production_run_repo,
        consumption_repo: IMaterialConsumptionRepository = material_consumption_repo,
        outbox_repo = None,
    ) -> None:
        self._repo = repository
        self._consumption_repo = consumption_repo
        self._outbox_repo = outbox_repo or outbox_repository

    async def _emit(self, ev: DomainEvent, session: Optional[Any] = None) -> None:
        # Synchronous request path offloads event dispatch to durable outbox worker
        await self._outbox_repo.append_domain_event(ev, session=session)

    async def create_production_run(
        self, organization_id: uuid.UUID, dto: ProductionRunCreateDTO, actor_id: uuid.UUID
    ) -> ProductionRunResponseDTO:
        site = await site_repo.get_by_id(dto.site_id)
        if not site or site.organization_id != organization_id:
            raise EntityNotFoundException("Site not found in this organization.")

        plant = await plant_repo.get_by_id(dto.plant_id)
        if not plant or plant.organization_id != organization_id:
            raise EntityNotFoundException("Plant not found in this organization.")

        line = await production_line_repo.get_by_id(dto.production_line_id)
        if not line or line.organization_id != organization_id:
            raise EntityNotFoundException("Production line not found in this organization.")

        wo = await work_order_repo.get_by_id(dto.work_order_id)
        if not wo or wo.organization_id != organization_id:
            raise EntityNotFoundException("Referenced Work Order not found in this organization.")

        if dto.machine_id:
            machine = await machine_repo.get_by_id(dto.machine_id)
            if not machine or machine.organization_id != organization_id:
                raise EntityNotFoundException("Machine not found in this organization.")

        existing = await self._repo.get_by_number(organization_id, dto.run_number)
        if existing:
            raise EntityAlreadyExistsException(
                f"Production run with number '{dto.run_number}' already exists in organization."
            )

        run = ProductionRun(
            organization_id=organization_id,
            site_id=dto.site_id,
            plant_id=dto.plant_id,
            production_line_id=dto.production_line_id,
            work_order_id=dto.work_order_id,
            machine_id=dto.machine_id,
            run_number=dto.run_number,
            product_code=dto.product_code,
            planned_quantity=dto.planned_quantity,
            unit_of_measure=dto.unit_of_measure,
            operator_id=dto.operator_id or actor_id,
            notes=dto.notes,
        )
        saved = await self._repo.add(run)

        await self._emit(
            DomainEvent(
                event_type="ProductionRunCreated",
                aggregate_id=str(saved.id),
                aggregate_type="ProductionRun",
                organization_id=str(organization_id),
                payload={"run_number": saved.run_number, "work_order_id": str(saved.work_order_id)},
            )
        )

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="PRODUCTION_RUN_CREATED",
            resource_type="ProductionRun",
            resource_id=saved.id,
            metadata={"run_number": saved.run_number, "product_code": saved.product_code},
        )
        return self._to_dto(saved)

    async def get_production_run(self, organization_id: uuid.UUID, run_id: uuid.UUID) -> ProductionRunResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")
        return self._to_dto(run)

    async def list_production_runs(
        self,
        organization_id: uuid.UUID,
        production_line_id: Optional[uuid.UUID] = None,
        work_order_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ProductionRunResponseDTO]:
        runs = await self._repo.list_by_organization(
            organization_id,
            production_line_id=production_line_id,
            work_order_id=work_order_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        return [self._to_dto(r) for r in runs]

    async def start_production_run(
        self, organization_id: uuid.UUID, run_id: uuid.UUID, actor_id: uuid.UUID
    ) -> ProductionRunResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")

        run.start(operator_id=actor_id)
        updated = await self._repo.update(run)
        for event in run.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="PRODUCTION_RUN_STARTED",
            resource_type="ProductionRun",
            resource_id=updated.id,
            metadata={"run_number": updated.run_number},
        )
        return self._to_dto(updated)

    async def pause_production_run(
        self, organization_id: uuid.UUID, run_id: uuid.UUID, actor_id: uuid.UUID
    ) -> ProductionRunResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")

        run.pause()
        updated = await self._repo.update(run)
        for event in run.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="PRODUCTION_RUN_PAUSED",
            resource_type="ProductionRun",
            resource_id=updated.id,
            metadata={"run_number": updated.run_number},
        )
        return self._to_dto(updated)

    async def resume_production_run(
        self, organization_id: uuid.UUID, run_id: uuid.UUID, actor_id: uuid.UUID
    ) -> ProductionRunResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")

        run.resume()
        updated = await self._repo.update(run)
        for event in run.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="PRODUCTION_RUN_RESUMED",
            resource_type="ProductionRun",
            resource_id=updated.id,
            metadata={"run_number": updated.run_number},
        )
        return self._to_dto(updated)

    async def record_quantity(
        self, organization_id: uuid.UUID, run_id: uuid.UUID, dto: ProductionQuantityRecordDTO, actor_id: uuid.UUID
    ) -> ProductionRunResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")

        run.record_quantity(good_quantity=dto.good_quantity, rejected_quantity=dto.rejected_quantity)
        updated = await self._repo.update(run)
        for event in run.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="PRODUCTION_QUANTITY_RECORDED",
            resource_type="ProductionRun",
            resource_id=updated.id,
            metadata={
                "run_number": updated.run_number,
                "good": dto.good_quantity,
                "rejected": dto.rejected_quantity,
                "actual_total": updated.actual_quantity,
            },
        )
        return self._to_dto(updated)

    async def complete_production_run(
        self, organization_id: uuid.UUID, run_id: uuid.UUID, actor_id: uuid.UUID
    ) -> ProductionRunResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")

        run.complete()
        updated = await self._repo.update(run)
        for event in run.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="PRODUCTION_RUN_COMPLETED",
            resource_type="ProductionRun",
            resource_id=updated.id,
            metadata={"run_number": updated.run_number, "actual_quantity": updated.actual_quantity},
        )
        return self._to_dto(updated)

    async def abort_production_run(
        self, organization_id: uuid.UUID, run_id: uuid.UUID, reason: str, actor_id: uuid.UUID
    ) -> ProductionRunResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")

        run.abort(reason=reason)
        updated = await self._repo.update(run)
        for event in run.collect_events():
            await self._emit(event)

        await audit_service.log_action(
            actor_id=actor_id,
            organization_id=organization_id,
            action="PRODUCTION_RUN_ABORTED",
            resource_type="ProductionRun",
            resource_id=updated.id,
            metadata={"run_number": updated.run_number, "reason": reason},
        )
        return self._to_dto(updated)

    async def consume_material(
        self, organization_id: uuid.UUID, run_id: uuid.UUID, dto: MaterialConsumeDTO, actor_id: uuid.UUID
    ) -> MaterialConsumptionResponseDTO:
        run = await self._repo.get_by_id(run_id)
        if not run or run.organization_id != organization_id:
            raise EntityNotFoundException("Production run not found in this organization.")

        tx = await inventory_service.consume_material(
            organization_id=organization_id,
            consumer_type=ConsumerType.PRODUCTION_RUN.value,
            consumer_id=run.id,
            item_id=dto.item_id,
            location_id=dto.location_id,
            quantity=dto.quantity,
            actor_id=actor_id,
        )

        consumption = MaterialConsumption(
            organization_id=organization_id,
            consumer_type=ConsumerType.PRODUCTION_RUN.value,
            consumer_id=run.id,
            item_id=dto.item_id,
            location_id=dto.location_id,
            quantity=dto.quantity,
            inventory_transaction_id=tx.id,
            consumed_by=actor_id,
        )
        saved = await self._consumption_repo.add(consumption)

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

    def _to_dto(self, r: ProductionRun) -> ProductionRunResponseDTO:
        return ProductionRunResponseDTO(
            id=r.id,
            organization_id=r.organization_id,
            site_id=r.site_id,
            plant_id=r.plant_id,
            production_line_id=r.production_line_id,
            machine_id=r.machine_id,
            work_order_id=r.work_order_id,
            run_number=r.run_number,
            product_code=r.product_code,
            planned_quantity=r.planned_quantity,
            actual_quantity=r.actual_quantity,
            rejected_quantity=r.rejected_quantity,
            unit_of_measure=r.unit_of_measure,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            operator_id=r.operator_id,
            notes=r.notes,
            version=r.version,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )


# Singleton service instances
work_order_service = WorkOrderService()
production_run_service = ProductionRunService()
