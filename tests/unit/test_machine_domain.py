"""Unit tests for Machine domain entity and operational state machine."""

import unittest
import uuid

from industrial_oracle.assets.domain.models import Machine, MachineStatus
from industrial_oracle.core.exceptions import BusinessRuleViolationException


class TestMachineDomain(unittest.TestCase):
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.asset_id = uuid.uuid4()
        self.machine = Machine(
            organization_id=self.org_id,
            asset_id=self.asset_id,
            name="Injection Molding Unit 1",
            power_rating_kw=75.5,
            operating_hours=1200.0,
        )

    def test_initial_state(self):
        self.assertEqual(self.machine.status, MachineStatus.STOPPED.value)
        self.assertEqual(self.machine.power_rating_kw, 75.5)
        self.assertEqual(self.machine.operating_hours, 1200.0)

    def test_start_and_stop_lifecycle(self):
        self.machine.start()
        self.assertEqual(self.machine.status, MachineStatus.RUNNING.value)

        self.machine.stop()
        self.assertEqual(self.machine.status, MachineStatus.STOPPED.value)

    def test_fault_lifecycle_and_invariants(self):
        self.machine.start()
        self.machine.record_fault(fault_code="ERR-OVERHEAT", description="Hydraulic fluid temperature critical")
        self.assertEqual(self.machine.status, MachineStatus.FAULTED.value)
        self.assertEqual(self.machine.fault_code, "ERR-OVERHEAT")

        # Invariant: Machine cannot start while FAULTED
        with self.assertRaises(BusinessRuleViolationException):
            self.machine.start()

        # Clear fault
        self.machine.clear_fault()
        self.assertEqual(self.machine.status, MachineStatus.STOPPED.value)
        self.assertIsNone(self.machine.fault_code)

        # Can start after clearing fault
        self.machine.start()
        self.assertEqual(self.machine.status, MachineStatus.RUNNING.value)

    def test_maintenance_lifecycle(self):
        self.machine.set_maintenance()
        self.assertEqual(self.machine.status, MachineStatus.MAINTENANCE.value)

        with self.assertRaises(BusinessRuleViolationException):
            self.machine.start()

        self.machine.complete_maintenance()
        self.assertEqual(self.machine.status, MachineStatus.STOPPED.value)

    def test_operating_hours_tracking(self):
        self.machine.log_operating_hours(8.5)
        self.assertEqual(self.machine.operating_hours, 1208.5)

        with self.assertRaises(BusinessRuleViolationException):
            self.machine.log_operating_hours(-5.0)

    def test_domain_events_recording(self):
        self.machine.start()
        self.machine.stop()
        self.machine.record_fault("VIB-HIGH", "High vibration detected")

        events = self.machine.collect_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_type, "MachineStarted")
        self.assertEqual(events[1].event_type, "MachineStopped")
        self.assertEqual(events[2].event_type, "MachineFaultDetected")


if __name__ == "__main__":
    unittest.main()
