"""Unit tests for Maintenance Work Order domain model, lifecycle, and invariants."""

import unittest
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.maintenance.domain.maintenance_order import (
    MaintenanceStatus,
    MaintenanceType,
    MaintenanceWorkOrder,
)


class TestMaintenanceDomain(unittest.TestCase):
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.wo_id = uuid.uuid4()
        self.asset_id = uuid.uuid4()
        self.machine_id = uuid.uuid4()
        self.tech_id = uuid.uuid4()

    def test_creation_requires_equipment(self):
        # Fails when neither asset_id nor machine_id is provided
        with self.assertRaises(BusinessRuleViolationException):
            MaintenanceWorkOrder(
                organization_id=self.org_id,
                work_order_id=self.wo_id,
                maintenance_type=MaintenanceType.CORRECTIVE.value,
                fault_description="Bearing failure",
                asset_id=None,
                machine_id=None,
            )

    def test_initial_state_and_assignment(self):
        order = MaintenanceWorkOrder(
            organization_id=self.org_id,
            work_order_id=self.wo_id,
            maintenance_type=MaintenanceType.PREVENTIVE.value,
            fault_description="Quarterly motor inspection",
            machine_id=self.machine_id,
        )
        self.assertEqual(order.status, MaintenanceStatus.PLANNED.value)

        order.assign(technician_id=self.tech_id)
        self.assertEqual(order.status, MaintenanceStatus.ASSIGNED.value)
        self.assertEqual(order.technician_id, self.tech_id)

    def test_start_and_complete_lifecycle(self):
        order = MaintenanceWorkOrder(
            organization_id=self.org_id,
            work_order_id=self.wo_id,
            maintenance_type=MaintenanceType.EMERGENCY_REPAIR.value,
            fault_description="Hydraulic seal ruptured",
            asset_id=self.asset_id,
        )
        order.start()
        self.assertEqual(order.status, MaintenanceStatus.IN_PROGRESS.value)
        self.assertIsNotNone(order.maintenance_started_at)

        order.complete(
            corrective_action="Replaced O-ring and refilled hydraulic fluid",
            root_cause="Fatigue wear",
            downtime_minutes=45.0,
        )
        self.assertEqual(order.status, MaintenanceStatus.COMPLETED.value)
        self.assertEqual(order.downtime_minutes, 45.0)
        self.assertEqual(order.corrective_action, "Replaced O-ring and refilled hydraulic fluid")

        events = order.collect_events()
        types = [e.event_type for e in events]
        self.assertIn("MaintenanceStarted", types)
        self.assertIn("MaintenanceCompleted", types)

    def test_cancel_maintenance(self):
        order = MaintenanceWorkOrder(
            organization_id=self.org_id,
            work_order_id=self.wo_id,
            maintenance_type=MaintenanceType.INSPECTION.value,
            fault_description="Calibration inspection",
            asset_id=self.asset_id,
        )
        order.cancel(reason="Inspection postponed")
        self.assertEqual(order.status, MaintenanceStatus.CANCELLED.value)

        # Cannot cancel completed order
        order2 = MaintenanceWorkOrder(
            organization_id=self.org_id,
            work_order_id=self.wo_id,
            maintenance_type=MaintenanceType.INSPECTION.value,
            fault_description="Calibration inspection",
            asset_id=self.asset_id,
        )
        order2.start()
        order2.complete()
        with self.assertRaises(BusinessRuleViolationException):
            order2.cancel()


if __name__ == "__main__":
    unittest.main()
