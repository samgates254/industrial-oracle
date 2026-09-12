import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)
"""Tests for information-preserving demand order aggregation."""

import unittest
from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.normalization.demand import normalize_demand


class TestDemandAggregation(unittest.TestCase):
    """Demand order grouping and aggregation tests."""

    def test_demand_order_aggregation(self):
        orders = [
            DemandOrder(resource_id="FIN", period=2, quantity=10.0),
            DemandOrder(resource_id="FIN", period=2, quantity=15.0),
            DemandOrder(resource_id="FIN", period=1, quantity=5.0),
        ]
        norm_demand = normalize_demand(orders)

        self.assertEqual(norm_demand.demand_by_resource_period[("FIN", 2)], 25.0)
        self.assertEqual(norm_demand.demand_by_resource_period[("FIN", 1)], 5.0)
        self.assertEqual(len(norm_demand.orders), 2)
        self.assertEqual(norm_demand.orders[0].period, 1)
        self.assertEqual(norm_demand.orders[0].quantity, 5.0)
        self.assertEqual(norm_demand.orders[1].period, 2)
        self.assertEqual(norm_demand.orders[1].quantity, 25.0)


if __name__ == "__main__":
    unittest.main()
