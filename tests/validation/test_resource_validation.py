import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Resource validation."""

import unittest
from industrial_oracle.domain.enums import ResourceCategory
from industrial_oracle.domain.resources import Resource
from industrial_oracle.validation.exceptions import PhysicalValidationError, SchemaValidationError
from industrial_oracle.validation.physical import validate_resource


class TestResourceValidation(unittest.TestCase):
    """Unit tests for Resource validation."""

    def test_valid_resource_none_supply_cap(self):
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
            supply_cap=None,
        )
        validate_resource(res, num_periods=24)

    def test_negative_initial_stock(self):
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=-10.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
        )
        with self.assertRaises(PhysicalValidationError):
            validate_resource(res)

    def test_negative_safety_stock(self):
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=-5.0,
            max_storage=500.0,
            is_purchasable=True,
        )
        with self.assertRaises(PhysicalValidationError):
            validate_resource(res)

    def test_safety_stock_exceeds_max_storage(self):
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=600.0,
            max_storage=500.0,
            is_purchasable=True,
        )
        with self.assertRaises(PhysicalValidationError):
            validate_resource(res)

    def test_negative_supply_cap(self):
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
            supply_cap=[10.0, -5.0, 20.0],
        )
        with self.assertRaises(PhysicalValidationError):
            validate_resource(res, num_periods=3)

    def test_wrong_supply_cap_length(self):
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
            supply_cap=[10.0, 20.0],
        )
        with self.assertRaises(PhysicalValidationError):
            validate_resource(res, num_periods=24)

    def test_supply_cap_type_failure_raises_schema_error(self):
        """Regression test for M1.2.1: Non-list supply_cap raises SchemaValidationError."""
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
        )
        # Force a non-list supply_cap onto object to test Level 1 schema check
        object.__setattr__(res, 'supply_cap', 'invalid_string_cap')
        with self.assertRaises(SchemaValidationError):
            validate_resource(res, num_periods=24)

    def test_empty_resource_id(self):
        res = Resource(
            resource_id="   ",
            category=ResourceCategory.RAW,
            initial_stock=100.0,
            safety_stock=10.0,
            max_storage=500.0,
            is_purchasable=True,
        )
        with self.assertRaises(SchemaValidationError):
            validate_resource(res)


if __name__ == "__main__":
    unittest.main()
