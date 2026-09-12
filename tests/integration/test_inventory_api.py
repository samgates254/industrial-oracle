"""Integration tests for Inventory Items, Locations, Receipts, Issues, Adjustments, Transfers, and Balances."""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
    plant_repo,
    site_repo,
)


class TestInventoryAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Inv Test Org", slug=f"inv-org-{uuid.uuid4().hex[:6]}")
        self.site = Site(organization_id=self.org.id, name="Inv Site", code="IS-1")
        self.plant = Plant(organization_id=self.org.id, site_id=self.site.id, name="Inv Plant", code="IP-1")

        self.engineer = User(
            email=f"inv_eng_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Inventory Engineer",
        )
        self.membership = Membership(user_id=self.engineer.id, organization_id=self.org.id, role="ENGINEER")

        async def init():
            await organization_repo.add(self.org)
            await site_repo.add(self.site)
            await plant_repo.add(self.plant)
            await user_repo.add(self.engineer)
            await membership_repo.add(self.membership)

        asyncio.run(init())
        self.token = create_access_token(self.engineer.id, self.engineer.email)

    def test_item_and_location_lifecycle(self):
        sku = f"SKU-ALU-{uuid.uuid4().hex[:6].upper()}"
        item_res = self.client.post(
            "/api/v1/items",
            json={
                "sku": sku,
                "name": "Aluminum Ingot 99.7%",
                "unit_of_measure": "KG",
                "category": "RAW_MATERIAL",
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(item_res.status_code, 201)
        item_id = item_res.json()["id"]

        # Duplicate SKU in same org rejected
        dup_res = self.client.post(
            "/api/v1/items",
            json={"sku": sku, "name": "Duplicate Item", "unit_of_measure": "KG"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(dup_res.status_code, 409)

        # Create Location
        loc_res = self.client.post(
            "/api/v1/inventory/locations",
            json={"site_id": str(self.site.id), "code": "RACK-A1", "name": "Storage Rack A1"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(loc_res.status_code, 201)
        loc_id = loc_res.json()["id"]

    def test_stock_receipt_issue_and_insufficient_rejection(self):
        # Create item & location
        item_res = self.client.post(
            "/api/v1/items",
            json={"sku": f"SKU-LUB-{uuid.uuid4().hex[:6].upper()}", "name": "Industrial Lubricant ISO 68", "unit_of_measure": "L"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        item_id = item_res.json()["id"]

        loc_res = self.client.post(
            "/api/v1/inventory/locations",
            json={"site_id": str(self.site.id), "code": f"LOC-{uuid.uuid4().hex[:4].upper()}", "name": "Main Store"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        loc_id = loc_res.json()["id"]

        # 1. Receive Stock (100 L)
        rec_res = self.client.post(
            "/api/v1/inventory/receipts",
            json={"item_id": item_id, "location_id": loc_id, "quantity": 100.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(rec_res.status_code, 201)
        self.assertEqual(rec_res.json()["quantity"], 100.0)
        self.assertEqual(rec_res.json()["available_quantity"], 100.0)

        # 2. Issue Stock (30 L)
        issue_res = self.client.post(
            "/api/v1/inventory/issues",
            json={"item_id": item_id, "location_id": loc_id, "quantity": 30.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(issue_res.status_code, 200)
        self.assertEqual(issue_res.json()["quantity"], 70.0)

        # 3. Issue Excess Stock (80 L when only 70 L available) -> 422 BusinessRuleViolation
        excess_res = self.client.post(
            "/api/v1/inventory/issues",
            json={"item_id": item_id, "location_id": loc_id, "quantity": 80.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(excess_res.status_code, 422)
        self.assertEqual(excess_res.json()["error"]["code"], "BUSINESS_RULE_VIOLATION")

    def test_stock_transfer_between_locations(self):
        # Create item
        item_res = self.client.post(
            "/api/v1/items",
            json={"sku": f"SKU-BOLT-{uuid.uuid4().hex[:6].upper()}", "name": "M12 High-Strength Bolts", "unit_of_measure": "PCS"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        item_id = item_res.json()["id"]

        # Create two locations
        loc1_res = self.client.post(
            "/api/v1/inventory/locations",
            json={"site_id": str(self.site.id), "code": f"SRC-{uuid.uuid4().hex[:4].upper()}", "name": "Warehouse Alpha"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        loc1_id = loc1_res.json()["id"]

        loc2_res = self.client.post(
            "/api/v1/inventory/locations",
            json={"site_id": str(self.site.id), "code": f"DST-{uuid.uuid4().hex[:4].upper()}", "name": "Line Staging Beta"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        loc2_id = loc2_res.json()["id"]

        # Receive 500 PCS into loc1
        self.client.post(
            "/api/v1/inventory/receipts",
            json={"item_id": item_id, "location_id": loc1_id, "quantity": 500.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )

        # Transfer 200 PCS from loc1 to loc2
        tx_res = self.client.post(
            "/api/v1/inventory/transfers",
            json={"item_id": item_id, "source_location_id": loc1_id, "destination_location_id": loc2_id, "quantity": 200.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(tx_res.status_code, 200)
        balances = tx_res.json()
        self.assertEqual(len(balances), 2)
        # Check source now 300, dest now 200
        src_bal = next(b for b in balances if b["location_id"] == loc1_id)
        dest_bal = next(b for b in balances if b["location_id"] == loc2_id)
        self.assertEqual(src_bal["quantity"], 300.0)
        self.assertEqual(dest_bal["quantity"], 200.0)


if __name__ == "__main__":
    unittest.main()
