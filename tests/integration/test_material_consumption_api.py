"""Integration tests for Material Consumption in Production Runs and Maintenance Orders."""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.assets.domain.models import Asset, Machine, ProductionLine
from industrial_oracle.assets.infrastructure.repository import asset_repo, machine_repo, production_line_repo
from industrial_oracle.core.security import create_access_token, hash_password
from industrial_oracle.identity.domain.models import User
from industrial_oracle.identity.infrastructure.repository import user_repo
from industrial_oracle.operations.domain.production_run import ProductionRun
from industrial_oracle.operations.domain.work_order import WorkOrder
from industrial_oracle.operations.infrastructure.repository import production_run_repo, work_order_repo
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
    plant_repo,
    site_repo,
)


class TestMaterialConsumptionAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Consumption Org", slug=f"cons-org-{uuid.uuid4().hex[:6]}")
        self.site = Site(organization_id=self.org.id, name="Cons Site", code="CS-1")
        self.plant = Plant(organization_id=self.org.id, site_id=self.site.id, name="Cons Plant", code="CP-1")
        self.line = ProductionLine(organization_id=self.org.id, plant_id=self.plant.id, name="Assembly Line", code="AL-1")
        self.asset = Asset(
            organization_id=self.org.id,
            plant_id=self.plant.id,
            name="Packaging Robot",
            asset_tag=f"ROB-{uuid.uuid4().hex[:4].upper()}",
            asset_type="ROBOTIC",
        )
        self.machine = Machine(
            organization_id=self.org.id,
            asset_id=self.asset.id,
            name="Robot Arm 1",
        )
        self.wo = WorkOrder(
            organization_id=self.org.id,
            site_id=self.site.id,
            plant_id=self.plant.id,
            work_order_number=f"WO-C-{uuid.uuid4().hex[:6].upper()}",
            title="Consumables Host Order",
        )
        self.run = ProductionRun(
            organization_id=self.org.id,
            site_id=self.site.id,
            plant_id=self.plant.id,
            production_line_id=self.line.id,
            work_order_id=self.wo.id,
            run_number=f"PR-C-{uuid.uuid4().hex[:6].upper()}",
            product_code="FINAL-SKU",
            planned_quantity=100.0,
            unit_of_measure="PCS",
        )

        self.engineer = User(
            email=f"cons_eng_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Consumption Engineer",
        )
        self.membership = Membership(user_id=self.engineer.id, organization_id=self.org.id, role="ENGINEER")

        async def init():
            await organization_repo.add(self.org)
            await site_repo.add(self.site)
            await plant_repo.add(self.plant)
            await production_line_repo.add(self.line)
            await asset_repo.add(self.asset)
            await machine_repo.add(self.machine)
            await work_order_repo.add(self.wo)
            await production_run_repo.add(self.run)
            await user_repo.add(self.engineer)
            await membership_repo.add(self.membership)

        asyncio.run(init())
        self.token = create_access_token(self.engineer.id, self.engineer.email)

        # Seed an item and location with stock (100 units)
        item_res = self.client.post(
            "/api/v1/items",
            json={"sku": f"RESIN-{uuid.uuid4().hex[:4].upper()}", "name": "Epoxy Resin", "unit_of_measure": "KG"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.item_id = item_res.json()["id"]

        loc_res = self.client.post(
            "/api/v1/inventory/locations",
            json={"site_id": str(self.site.id), "code": f"BIN-{uuid.uuid4().hex[:4].upper()}", "name": "Resin Bin"},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.loc_id = loc_res.json()["id"]

        # Receive 100 KG
        self.client.post(
            "/api/v1/inventory/receipts",
            json={"item_id": self.item_id, "location_id": self.loc_id, "quantity": 100.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )

    def test_production_run_material_consumption(self):
        # Consume 25 KG in production run
        res = self.client.post(
            f"/api/v1/production-runs/{self.run.id}/materials/consume",
            json={"item_id": self.item_id, "location_id": self.loc_id, "quantity": 25.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 201)
        cons = res.json()
        self.assertEqual(cons["consumer_type"], "PRODUCTION_RUN")
        self.assertEqual(cons["consumer_id"], str(self.run.id))
        self.assertEqual(cons["quantity"], 25.0)

        # Verify stock balance decremented from 100 to 75
        bal_res = self.client.get(
            f"/api/v1/inventory/balances?item_id={self.item_id}&location_id={self.loc_id}",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(bal_res.status_code, 200)
        self.assertEqual(bal_res.json()[0]["quantity"], 75.0)

    def test_maintenance_material_consumption(self):
        # Create a maintenance work order
        maint_res = self.client.post(
            "/api/v1/maintenance/work-orders",
            json={
                "site_id": str(self.site.id),
                "plant_id": str(self.plant.id),
                "work_order_number": f"WO-M-PART-{uuid.uuid4().hex[:4].upper()}",
                "title": "Seal Replacement",
                "fault_description": "Degraded gasket",
                "machine_id": str(self.machine.id),
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        maint_id = maint_res.json()["id"]

        # Consume 10 KG resin in maintenance
        res = self.client.post(
            f"/api/v1/maintenance/work-orders/{maint_id}/materials/consume",
            json={"item_id": self.item_id, "location_id": self.loc_id, "quantity": 10.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 201)
        cons = res.json()
        self.assertEqual(cons["consumer_type"], "MAINTENANCE_WORK_ORDER")
        self.assertEqual(cons["consumer_id"], str(maint_id))
        self.assertEqual(cons["quantity"], 10.0)

    def test_insufficient_stock_consumption_rejected(self):
        # Attempt to consume 200 KG when only 100 KG exists
        res = self.client.post(
            f"/api/v1/production-runs/{self.run.id}/materials/consume",
            json={"item_id": self.item_id, "location_id": self.loc_id, "quantity": 200.0},
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 422)
        self.assertEqual(res.json()["error"]["code"], "BUSINESS_RULE_VIOLATION")


if __name__ == "__main__":
    unittest.main()
