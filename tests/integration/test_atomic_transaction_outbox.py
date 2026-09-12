"""Integration tests verifying atomic business state mutation + outbox event persistence."""

import asyncio
import unittest
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.integrations.infrastructure.repository import InMemoryOutboxRepository
from industrial_oracle.inventory.application.dtos import InventoryReceiptDTO
from industrial_oracle.inventory.application.services import InventoryService
from industrial_oracle.inventory.domain.models import InventoryLocation, Item
from industrial_oracle.inventory.infrastructure.repository import (
    InMemoryInventoryBalanceRepository,
    InMemoryInventoryLocationRepository,
    InMemoryInventoryTransactionRepository,
    InMemoryItemRepository,
)
from industrial_oracle.operations.application.dtos import ProductionRunCreateDTO, WorkOrderCreateDTO
from industrial_oracle.operations.application.services import ProductionRunService, WorkOrderService
from industrial_oracle.operations.domain.work_order import WorkOrder, WorkOrderStatus, WorkOrderType
from industrial_oracle.operations.infrastructure.repository import (
    InMemoryMaterialConsumptionRepository,
    InMemoryProductionRunRepository,
    InMemoryWorkOrderRepository,
)


class TestAtomicTransactionOutbox(unittest.TestCase):
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.site_id = uuid.uuid4()
        self.plant_id = uuid.uuid4()
        self.actor_id = uuid.uuid4()
        self.outbox_repo = InMemoryOutboxRepository()

    def test_work_order_completion_atomically_appends_outbox_event(self):
        async def run():
            wo_repo = InMemoryWorkOrderRepository()
            wo_svc = WorkOrderService(repository=wo_repo, outbox_repo=self.outbox_repo)

            # Create a released work order
            wo = WorkOrder(
                organization_id=self.org_id,
                site_id=self.site_id,
                plant_id=self.plant_id,
                title="CNC Bearing Replacement",
                work_order_type=WorkOrderType.MAINTENANCE,
                work_order_number="WO-ATOMIC-1",
            )
            wo.release()
            wo.start()
            await wo_repo.add(wo)

            # Complete work order
            completed_dto = await wo_svc.complete_work_order(self.org_id, wo.id, self.actor_id)
            self.assertEqual(completed_dto.status, "COMPLETED")

            # Verify OutboxEvent was created atomically in the outbox repository
            outbox_events, total = await self.outbox_repo.query_events(
                organization_id=str(self.org_id),
                aggregate_id=str(wo.id),
                aggregate_type="WorkOrder",
            )
            self.assertGreaterEqual(total, 1)
            event_types = [ev.event_type for ev in outbox_events]
            self.assertIn("WorkOrderCompleted.v1", event_types)

        asyncio.run(run())

    def test_production_run_execution_atomically_appends_outbox_events(self):
        async def run():
            from industrial_oracle.organization.domain.models import Site, Plant
            from industrial_oracle.organization.infrastructure.repository import site_repo, plant_repo
            from industrial_oracle.assets.domain.models import ProductionLine
            from industrial_oracle.assets.infrastructure.repository import production_line_repo

            # Register site, plant, line so creation validation passes
            site = Site(id=self.site_id, organization_id=self.org_id, name="Test Site", code="SITE-1")
            plant = Plant(id=self.plant_id, organization_id=self.org_id, site_id=self.site_id, name="Test Plant", code="PLANT-1")
            line = ProductionLine(organization_id=self.org_id, plant_id=self.plant_id, name="Line 1", code="LINE-1")
            await site_repo.add(site)
            await plant_repo.add(plant)
            await production_line_repo.add(line)

            from industrial_oracle.operations.infrastructure.repository import work_order_repo
            run_repo = InMemoryProductionRunRepository()
            consumption_repo = InMemoryMaterialConsumptionRepository()
            run_svc = ProductionRunService(
                repository=run_repo,
                consumption_repo=consumption_repo,
                outbox_repo=self.outbox_repo,
            )

            # Setup released work order
            wo = WorkOrder(
                organization_id=self.org_id,
                site_id=self.site_id,
                plant_id=self.plant_id,
                title="Batch Production Run",
                work_order_type=WorkOrderType.PRODUCTION,
                work_order_number="WO-RUN-1",
            )
            wo.release()
            await work_order_repo.add(wo)

            # Create production run
            dto = ProductionRunCreateDTO(
                site_id=self.site_id,
                plant_id=self.plant_id,
                work_order_id=wo.id,
                production_line_id=line.id,
                run_number="RUN-ATOMIC-1",
                product_code="ITEM-X",
                planned_quantity=100.0,
                unit_of_measure="UNITS",
            )
            created_run = await run_svc.create_production_run(self.org_id, dto, self.actor_id)
            self.assertEqual(created_run.status, "PLANNED")

            # Verify outbox event recorded
            events, total = await self.outbox_repo.query_events(
                organization_id=str(self.org_id),
                aggregate_id=str(created_run.id),
                aggregate_type="ProductionRun",
            )
            self.assertEqual(total, 1)
            self.assertEqual(events[0].event_type, "ProductionRunCreated.v1")

        asyncio.run(run())

    def test_inventory_movement_atomically_appends_outbox_event(self):
        async def run():
            item_repo = InMemoryItemRepository()
            loc_repo = InMemoryInventoryLocationRepository()
            bal_repo = InMemoryInventoryBalanceRepository()
            tx_repo = InMemoryInventoryTransactionRepository()

            inv_svc = InventoryService(
                item_repository=item_repo,
                location_repository=loc_repo,
                balance_repository=bal_repo,
                transaction_repository=tx_repo,
                outbox_repo=self.outbox_repo,
            )

            # Seed item and location
            item = Item(
                organization_id=self.org_id,
                sku="SKU-STEEL-100",
                name="Steel Rods",
                unit_of_measure="KG",
            )
            await item_repo.add(item)
            loc = InventoryLocation(
                organization_id=self.org_id,
                site_id=self.site_id,
                code="BAY-A1",
                name="Bay A1",
            )
            await loc_repo.add(loc)

            # Inbound receipt
            receipt_dto = InventoryReceiptDTO(item_id=item.id, location_id=loc.id, quantity=150.0)
            bal = await inv_svc.receive_stock(self.org_id, receipt_dto, self.actor_id)
            self.assertEqual(bal.quantity, 150.0)

            # Verify Outbox record
            events, total = await self.outbox_repo.query_events(
                organization_id=str(self.org_id),
                event_type="InventoryReceived",
            )
            self.assertEqual(total, 1)
            self.assertEqual(events[0].aggregate_type, "InventoryBalance")
            self.assertEqual(events[0].payload["quantity"], 150.0)

        asyncio.run(run())

    def test_simulated_transaction_rollback_preserves_no_outbox_or_state(self):
        async def run():
            wo_repo = InMemoryWorkOrderRepository()
            wo_svc = WorkOrderService(repository=wo_repo, outbox_repo=self.outbox_repo)

            # Create a DRAFT work order
            wo = WorkOrder(
                organization_id=self.org_id,
                site_id=self.site_id,
                plant_id=self.plant_id,
                title="Draft Work Order",
                work_order_type=WorkOrderType.PRODUCTION,
                work_order_number="WO-ROLLBACK-1",
            )
            await wo_repo.add(wo)

            # Attempting to start a DRAFT work order directly violates state machine rules and must fail
            with self.assertRaises(BusinessRuleViolationException):
                await wo_svc.start_work_order(self.org_id, wo.id, self.actor_id)

            # Verify NO state mutation occurred (still DRAFT)
            current_wo = await wo_repo.get_by_id(wo.id)
            self.assertEqual(current_wo.status, WorkOrderStatus.DRAFT)

            # Verify NO start event was appended to outbox
            events, total = await self.outbox_repo.query_events(
                organization_id=str(self.org_id),
                event_type="WorkOrderStarted",
            )
            self.assertEqual(total, 0)

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
