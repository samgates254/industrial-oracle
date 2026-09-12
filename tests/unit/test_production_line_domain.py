"""Unit tests for ProductionLine domain model."""

import unittest
import uuid

from industrial_oracle.assets.domain.models import ProductionLine, ProductionLineStatus


class TestProductionLineDomain(unittest.TestCase):
    def test_production_line_status_lifecycle(self):
        line = ProductionLine(
            organization_id=uuid.uuid4(),
            plant_id=uuid.uuid4(),
            name="Assembly Line Alpha",
            code="LINE-A",
            capacity_units_per_hour=350.0,
        )
        self.assertEqual(line.status, ProductionLineStatus.ACTIVE.value)
        self.assertEqual(line.capacity_units_per_hour, 350.0)

        line.deactivate()
        self.assertEqual(line.status, ProductionLineStatus.INACTIVE.value)

        line.set_maintenance()
        self.assertEqual(line.status, ProductionLineStatus.MAINTENANCE.value)

        line.activate()
        self.assertEqual(line.status, ProductionLineStatus.ACTIVE.value)


if __name__ == "__main__":
    unittest.main()
