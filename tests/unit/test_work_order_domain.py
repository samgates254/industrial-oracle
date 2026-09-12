"""Unit tests for Work Order domain models, invariants, and state transitions."""

import unittest
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.operations.domain.work_order import (
    WorkOrder,
    WorkOrderPriority,
    WorkOrderStatus,
    WorkOrderType,
)


class TestWorkOrderDomain(unittest.TestCase):
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.site_id = uuid.uuid4()
        self.plant_id = uuid.uuid4()

    def test_initial_state_is_draft(self):
        wo = WorkOrder(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            work_order_number="WO-001",
            title="Assemble Widget A",
        )
        self.assertEqual(wo.status, WorkOrderStatus.DRAFT.value)
        self.assertEqual(wo.work_order_type, WorkOrderType.PRODUCTION.value)
        self.assertEqual(wo.priority, WorkOrderPriority.MEDIUM.value)
        self.assertEqual(wo.version, 1)

    def test_release_transition(self):
        wo = WorkOrder(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            work_order_number="WO-002",
            title="Release Test",
        )
        wo.release()
        self.assertEqual(wo.status, WorkOrderStatus.RELEASED.value)
        self.assertEqual(wo.version, 2)
        events = wo.collect_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "WorkOrderReleased")

    def test_start_transition(self):
        wo = WorkOrder(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            work_order_number="WO-003",
            title="Start Test",
        )
        wo.release()
        wo.start()
        self.assertEqual(wo.status, WorkOrderStatus.IN_PROGRESS.value)
        self.assertIsNotNone(wo.actual_start)
        events = wo.collect_events()
        self.assertTrue(any(e.event_type == "WorkOrderStarted" for e in events))

    def test_hold_and_resume_transitions(self):
        wo = WorkOrder(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            work_order_number="WO-004",
            title="Hold Resume Test",
        )
        wo.release()
        wo.start()
        wo.put_on_hold(reason="Waiting for parts")
        self.assertEqual(wo.status, WorkOrderStatus.ON_HOLD.value)

        wo.resume()
        self.assertEqual(wo.status, WorkOrderStatus.IN_PROGRESS.value)
        events = wo.collect_events()
        types = [e.event_type for e in events]
        self.assertIn("WorkOrderPutOnHold", types)
        self.assertIn("WorkOrderResumed", types)

    def test_complete_transition(self):
        wo = WorkOrder(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            work_order_number="WO-005",
            title="Complete Test",
        )
        wo.release()
        wo.start()
        wo.complete()
        self.assertEqual(wo.status, WorkOrderStatus.COMPLETED.value)
        self.assertIsNotNone(wo.actual_end)

    def test_cancel_transition(self):
        wo = WorkOrder(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            work_order_number="WO-006",
            title="Cancel Test",
        )
        wo.cancel(reason="Order superseded")
        self.assertEqual(wo.status, WorkOrderStatus.CANCELLED.value)

    def test_invalid_state_transitions_raise_exception(self):
        wo = WorkOrder(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            work_order_number="WO-007",
            title="Invalid Transition Test",
        )
        # Cannot start from DRAFT
        with self.assertRaises(BusinessRuleViolationException):
            wo.start()

        # Cannot complete from DRAFT
        with self.assertRaises(BusinessRuleViolationException):
            wo.complete()

        # Release and start
        wo.release()
        wo.start()
        wo.complete()

        # Cannot cancel completed work order
        with self.assertRaises(BusinessRuleViolationException):
            wo.cancel()


if __name__ == "__main__":
    unittest.main()
