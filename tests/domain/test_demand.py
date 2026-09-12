import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Demand domain entity."""

import unittest
from industrial_oracle.domain.demand import DemandOrder


class TestDemandDomain(unittest.TestCase):
    """Demand domain representation tests."""

    def test_create_demand_order(self):
        """Test 6: Create demand for FINISHED at period 24 with quantity 150 kg."""
        order = DemandOrder(
            resource_id="FINISHED",
            period=24,
            quantity=150.0,
        )
        self.assertEqual(order.resource_id, "FINISHED")
        self.assertEqual(order.period, 24)
        self.assertEqual(order.quantity, 150.0)


if __name__ == "__main__":
    unittest.main()
