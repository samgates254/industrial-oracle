import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for DemandOrder validation."""

import unittest
from industrial_oracle.domain.demand import DemandOrder
from industrial_oracle.validation.exceptions import PhysicalValidationError, SchemaValidationError
from industrial_oracle.validation.physical import validate_demand_order


class TestDemandValidation(unittest.TestCase):
    """Unit tests for DemandOrder validation."""

    def test_valid_demand_and_zero_quantity(self):
        order1 = DemandOrder(resource_id="FINISHED", period=24, quantity=150.0)
        validate_demand_order(order1, num_periods=24)

        order_zero = DemandOrder(resource_id="FINISHED", period=1, quantity=0.0)
        validate_demand_order(order_zero, num_periods=24)

    def test_negative_quantity(self):
        order = DemandOrder(resource_id="FINISHED", period=10, quantity=-20.0)
        with self.assertRaises(PhysicalValidationError):
            validate_demand_order(order, num_periods=24)

    def test_period_outside_horizon(self):
        order = DemandOrder(resource_id="FINISHED", period=25, quantity=100.0)
        with self.assertRaises(PhysicalValidationError):
            validate_demand_order(order, num_periods=24)

    def test_empty_resource_id(self):
        order = DemandOrder(resource_id="", period=5, quantity=100.0)
        with self.assertRaises(SchemaValidationError):
            validate_demand_order(order, num_periods=24)

    def test_non_int_period_raises_schema_error(self):
        """Regression test for M1.2.1: Non-int period in DemandOrder raises SchemaValidationError."""
        order = DemandOrder(resource_id="FINISHED", period=5, quantity=100.0)
        object.__setattr__(order, 'period', 5.5)
        with self.assertRaises(SchemaValidationError):
            validate_demand_order(order, num_periods=24)

        object.__setattr__(order, 'period', True)
        with self.assertRaises(SchemaValidationError):
            validate_demand_order(order, num_periods=24)


if __name__ == "__main__":
    unittest.main()
