"""Unit tests for Production Run domain models, quantity invariants, and state transitions."""

import unittest
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.operations.domain.production_run import (
    ProductionRun,
    ProductionRunStatus,
)


class TestProductionRunDomain(unittest.TestCase):
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.site_id = uuid.uuid4()
        self.plant_id = uuid.uuid4()
        self.line_id = uuid.uuid4()
        self.wo_id = uuid.uuid4()

    def test_initial_state_and_quantity_invariants(self):
        run = ProductionRun(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            production_line_id=self.line_id,
            work_order_id=self.wo_id,
            run_number="PR-001",
            product_code="PROD-A",
            planned_quantity=500.0,
            unit_of_measure="KG",
        )
        self.assertEqual(run.status, ProductionRunStatus.PLANNED.value)
        self.assertEqual(run.actual_quantity, 0.0)
        self.assertEqual(run.rejected_quantity, 0.0)

    def test_negative_quantity_rejected_on_creation(self):
        with self.assertRaises(BusinessRuleViolationException):
            ProductionRun(
                organization_id=self.org_id,
                site_id=self.site_id,
                plant_id=self.plant_id,
                production_line_id=self.line_id,
                work_order_id=self.wo_id,
                run_number="PR-NEG",
                product_code="PROD-A",
                planned_quantity=-10.0,
                unit_of_measure="KG",
            )

    def test_rejection_exceeding_actual_rejected_on_creation(self):
        with self.assertRaises(BusinessRuleViolationException):
            ProductionRun(
                organization_id=self.org_id,
                site_id=self.site_id,
                plant_id=self.plant_id,
                production_line_id=self.line_id,
                work_order_id=self.wo_id,
                run_number="PR-INV",
                product_code="PROD-A",
                planned_quantity=100.0,
                actual_quantity=50.0,
                rejected_quantity=60.0,  # 60 > 50
                unit_of_measure="KG",
            )

    def test_start_pause_resume_lifecycle(self):
        run = ProductionRun(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            production_line_id=self.line_id,
            work_order_id=self.wo_id,
            run_number="PR-002",
            product_code="PROD-B",
            planned_quantity=200.0,
            unit_of_measure="UNITS",
        )
        run.start()
        self.assertEqual(run.status, ProductionRunStatus.RUNNING.value)
        self.assertIsNotNone(run.started_at)

        run.pause()
        self.assertEqual(run.status, ProductionRunStatus.PAUSED.value)

        run.resume()
        self.assertEqual(run.status, ProductionRunStatus.RUNNING.value)

    def test_record_quantity_incrementally(self):
        run = ProductionRun(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            production_line_id=self.line_id,
            work_order_id=self.wo_id,
            run_number="PR-003",
            product_code="PROD-C",
            planned_quantity=100.0,
            unit_of_measure="UNITS",
        )
        run.start()
        run.record_quantity(good_quantity=40.0, rejected_quantity=2.0)
        self.assertEqual(run.actual_quantity, 42.0)
        self.assertEqual(run.rejected_quantity, 2.0)

        run.record_quantity(good_quantity=50.0, rejected_quantity=3.0)
        self.assertEqual(run.actual_quantity, 95.0)
        self.assertEqual(run.rejected_quantity, 5.0)

        events = run.collect_events()
        self.assertTrue(any(e.event_type == "ProductionQuantityRecorded" for e in events))

    def test_cannot_record_quantity_when_not_running(self):
        run = ProductionRun(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            production_line_id=self.line_id,
            work_order_id=self.wo_id,
            run_number="PR-004",
            product_code="PROD-D",
            planned_quantity=100.0,
            unit_of_measure="UNITS",
        )
        with self.assertRaises(BusinessRuleViolationException):
            run.record_quantity(good_quantity=10.0)

    def test_complete_and_abort_terminal_states(self):
        run = ProductionRun(
            organization_id=self.org_id,
            site_id=self.site_id,
            plant_id=self.plant_id,
            production_line_id=self.line_id,
            work_order_id=self.wo_id,
            run_number="PR-005",
            product_code="PROD-E",
            planned_quantity=100.0,
            unit_of_measure="UNITS",
        )
        run.start()
        run.record_quantity(good_quantity=100.0)
        run.complete()
        self.assertEqual(run.status, ProductionRunStatus.COMPLETED.value)
        self.assertIsNotNone(run.completed_at)

        # Cannot abort completed run
        with self.assertRaises(BusinessRuleViolationException):
            run.abort(reason="Too late")


if __name__ == "__main__":
    unittest.main()
