"""Unit tests for Asset domain entity and operational status state machine."""

import unittest
import uuid

from industrial_oracle.assets.domain.models import Asset, AssetStatus
from industrial_oracle.core.exceptions import BusinessRuleViolationException


class TestAssetDomain(unittest.TestCase):
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.plant_id = uuid.uuid4()
        self.asset = Asset(
            organization_id=self.org_id,
            plant_id=self.plant_id,
            name="Hydraulic Press 500T",
            asset_tag="AST-HP-500",
            asset_type="HYDRAULIC",
            critical=True,
        )

    def test_initial_state(self):
        self.assertEqual(self.asset.status, AssetStatus.IN_SERVICE.value)
        self.assertTrue(self.asset.critical)
        self.assertEqual(self.asset.asset_tag, "AST-HP-500")

    def test_state_transitions(self):
        # IN_SERVICE -> MAINTENANCE
        self.asset.send_to_maintenance()
        self.assertEqual(self.asset.status, AssetStatus.MAINTENANCE.value)

        # MAINTENANCE -> IN_SERVICE
        self.asset.return_to_service()
        self.assertEqual(self.asset.status, AssetStatus.IN_SERVICE.value)

        # IN_SERVICE -> OUT_OF_SERVICE
        self.asset.take_out_of_service()
        self.assertEqual(self.asset.status, AssetStatus.OUT_OF_SERVICE.value)

        # OUT_OF_SERVICE -> IN_SERVICE
        self.asset.return_to_service()
        self.assertEqual(self.asset.status, AssetStatus.IN_SERVICE.value)

        # Terminal transition -> DECOMMISSIONED
        self.asset.decommission()
        self.assertEqual(self.asset.status, AssetStatus.DECOMMISSIONED.value)

    def test_decommissioned_terminal_invariant(self):
        self.asset.decommission()

        with self.assertRaises(BusinessRuleViolationException):
            self.asset.return_to_service()

        with self.assertRaises(BusinessRuleViolationException):
            self.asset.send_to_maintenance()

        with self.assertRaises(BusinessRuleViolationException):
            self.asset.take_out_of_service()

        with self.assertRaises(BusinessRuleViolationException):
            self.asset.decommission()

    def test_domain_events_recorded(self):
        self.asset.send_to_maintenance()
        self.asset.decommission()

        events = self.asset.collect_events()
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, "AssetStatusChanged")
        self.assertEqual(events[1].event_type, "AssetDecommissioned")


if __name__ == "__main__":
    unittest.main()
