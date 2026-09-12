"""Unit tests for Inventory domain models, balance invariants, and optimistic locking."""

import unittest
import uuid

from industrial_oracle.core.exceptions import BusinessRuleViolationException
from industrial_oracle.inventory.domain.models import (
    InventoryBalance,
    InventoryLocation,
    Item,
    ItemCategory,
)


class TestInventoryDomain(unittest.TestCase):
    def setUp(self):
        self.org_id = uuid.uuid4()
        self.item_id = uuid.uuid4()
        self.loc_id = uuid.uuid4()
        self.site_id = uuid.uuid4()

    def test_item_creation_and_state(self):
        item = Item(
            organization_id=self.org_id,
            sku="RM-STEEL-01",
            name="Cold Rolled Steel Sheet",
            unit_of_measure="KG",
            category=ItemCategory.RAW_MATERIAL.value,
        )
        self.assertEqual(item.sku, "RM-STEEL-01")
        self.assertTrue(item.active)

        item.deactivate()
        self.assertFalse(item.active)
        item.activate()
        self.assertTrue(item.active)

    def test_inventory_location_creation(self):
        loc = InventoryLocation(
            organization_id=self.org_id,
            site_id=self.site_id,
            code="WH-BAY-1",
            name="Warehouse Bay 1",
        )
        self.assertEqual(loc.code, "WH-BAY-1")
        self.assertTrue(loc.active)

    def test_inventory_balance_initialization_and_available(self):
        bal = InventoryBalance(
            organization_id=self.org_id,
            item_id=self.item_id,
            location_id=self.loc_id,
            quantity=100.0,
            reserved_quantity=20.0,
        )
        self.assertEqual(bal.available_quantity, 80.0)
        self.assertEqual(bal.version, 1)

    def test_inventory_balance_negative_rejected(self):
        with self.assertRaises(BusinessRuleViolationException):
            InventoryBalance(
                organization_id=self.org_id,
                item_id=self.item_id,
                location_id=self.loc_id,
                quantity=-5.0,
            )

    def test_inventory_balance_over_reservation_rejected(self):
        with self.assertRaises(BusinessRuleViolationException):
            InventoryBalance(
                organization_id=self.org_id,
                item_id=self.item_id,
                location_id=self.loc_id,
                quantity=50.0,
                reserved_quantity=60.0,
            )

    def test_increase_and_decrease_balance(self):
        bal = InventoryBalance(
            organization_id=self.org_id,
            item_id=self.item_id,
            location_id=self.loc_id,
            quantity=50.0,
        )
        bal.increase(25.0)
        self.assertEqual(bal.quantity, 75.0)
        self.assertEqual(bal.version, 2)

        bal.decrease(30.0)
        self.assertEqual(bal.quantity, 45.0)
        self.assertEqual(bal.version, 3)

    def test_insufficient_inventory_decrease_rejected(self):
        bal = InventoryBalance(
            organization_id=self.org_id,
            item_id=self.item_id,
            location_id=self.loc_id,
            quantity=10.0,
        )
        with self.assertRaises(BusinessRuleViolationException) as ctx:
            bal.decrease(15.0)
        self.assertEqual(ctx.exception.rule_name, "INSUFFICIENT_INVENTORY")

    def test_adjust_balance(self):
        bal = InventoryBalance(
            organization_id=self.org_id,
            item_id=self.item_id,
            location_id=self.loc_id,
            quantity=50.0,
        )
        delta = bal.adjust(40.0)
        self.assertEqual(delta, -10.0)
        self.assertEqual(bal.quantity, 40.0)
        self.assertEqual(bal.version, 2)


if __name__ == "__main__":
    unittest.main()
