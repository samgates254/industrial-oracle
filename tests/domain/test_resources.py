import os
import sys

_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

"""Tests for Resource domain entity."""

import unittest
from industrial_oracle.domain.enums import ResourceCategory
from pydantic import ValidationError
from industrial_oracle.domain.resources import Resource


class TestResourceDomain(unittest.TestCase):
    """Resource domain representation tests."""

    def test_create_raw_resource(self):
        """Test 1: Create RAW resource with specified stock bounds."""
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=500.0,
            safety_stock=50.0,
            max_storage=1000.0,
            is_purchasable=True,
            supply_cap=None,
        )
        self.assertEqual(res.resource_id, "RAW")
        self.assertEqual(res.category, ResourceCategory.RAW)
        self.assertEqual(res.initial_stock, 500.0)
        self.assertEqual(res.safety_stock, 50.0)
        self.assertEqual(res.max_storage, 1000.0)
        self.assertTrue(res.is_purchasable)
        self.assertIsNone(res.supply_cap)

    def test_resource_immutability(self):
        """Test that Resource instance is frozen."""
        res = Resource(
            resource_id="RAW",
            category=ResourceCategory.RAW,
            initial_stock=500.0,
            safety_stock=50.0,
            max_storage=1000.0,
            is_purchasable=True,
        )
        with self.assertRaises((TypeError, ValidationError)):
            res.initial_stock = 600.0


if __name__ == "__main__":
    unittest.main()
