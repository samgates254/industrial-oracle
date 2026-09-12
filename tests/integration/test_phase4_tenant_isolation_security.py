"""Mandatory Phase 4 Cross-Tenant Security, Isolation, and IDOR Attack Test Suite.

Hard Security Invariants:
1. Tenant B must NEVER read, modify, release, start, or cancel Tenant A Work Orders.
2. Tenant B must NEVER access, modify, start, complete, or abort Tenant A Production Runs.
3. Tenant B must NEVER read or control Tenant A Maintenance Orders.
4. Tenant B must NEVER read, issue, adjust, transfer, or consume Tenant A Items, Locations, or Inventory.
5. Cross-tenant FK injections (e.g. creating a Run in Tenant B referencing Tenant A Work Order) MUST fail with 404.
6. Viewer and Analyst roles MUST be blocked from operational mutations with 403 Forbidden.
"""

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
from industrial_oracle.inventory.domain.models import InventoryBalance, InventoryLocation, Item
from industrial_oracle.inventory.infrastructure.repository import (
    inventory_balance_repo,
    inventory_location_repo,
    item_repo,
)
from industrial_oracle.maintenance.domain.maintenance_order import MaintenanceWorkOrder
from industrial_oracle.maintenance.infrastructure.repository import maintenance_order_repo
from industrial_oracle.operations.domain.production_run import ProductionRun
from industrial_oracle.operations.domain.work_order import WorkOrder
from industrial_oracle.operations.infrastructure.repository import (
    production_run_repo,
    work_order_repo,
)
from industrial_oracle.organization.domain.models import Membership, Organization, Plant, Site
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
    plant_repo,
    site_repo,
)


class TestPhase4TenantIsolationSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # ----------------------------------------------------------------------
        # Tenant Alpha Setup
        # ----------------------------------------------------------------------
        self.org_a = Organization(name="Tenant Alpha Corp", slug=f"alpha-{uuid.uuid4().hex[:6]}")
        self.site_a = Site(organization_id=self.org_a.id, name="Alpha Site", code="AS-1")
        self.plant_a = Plant(organization_id=self.org_a.id, site_id=self.site_a.id, name="Alpha Plant", code="AP-1")
        self.line_a = ProductionLine(organization_id=self.org_a.id, plant_id=self.plant_a.id, name="Alpha Line", code="AL-1")
        self.asset_a = Asset(organization_id=self.org_a.id, plant_id=self.plant_a.id, name="Alpha Press", asset_tag="TAG-A", asset_type="HYDRAULIC")
        self.machine_a = Machine(organization_id=self.org_a.id, asset_id=self.asset_a.id, name="Alpha Machine")
        self.wo_a = WorkOrder(
            organization_id=self.org_a.id,
            site_id=self.site_a.id,
            plant_id=self.plant_a.id,
            work_order_number="WO-ALPHA-100",
            title="Confidential Alpha Production Directive",
        )
        self.run_a = ProductionRun(
            organization_id=self.org_a.id,
            site_id=self.site_a.id,
            plant_id=self.plant_a.id,
            production_line_id=self.line_a.id,
            work_order_id=self.wo_a.id,
            run_number="RUN-ALPHA-100",
            product_code="SECRET-FORMULA-A",
            planned_quantity=1000.0,
            unit_of_measure="KG",
        )
        self.maint_a = MaintenanceWorkOrder(
            organization_id=self.org_a.id,
            work_order_id=self.wo_a.id,
            maintenance_type="PREVENTIVE",
            fault_description="Confidential Alpha Maintenance",
            machine_id=self.machine_a.id,
        )
        self.item_a = Item(
            organization_id=self.org_a.id,
            sku="SKU-SECRET-A",
            name="Proprietary Polymer A",
            unit_of_measure="KG",
        )
        self.loc_a = InventoryLocation(
            organization_id=self.org_a.id,
            site_id=self.site_a.id,
            code="VAULT-A",
            name="Alpha Secure Vault",
        )
        self.bal_a = InventoryBalance(
            organization_id=self.org_a.id,
            item_id=self.item_a.id,
            location_id=self.loc_a.id,
            quantity=500.0,
        )

        # ----------------------------------------------------------------------
        # Tenant Beta Setup
        # ----------------------------------------------------------------------
        self.org_b = Organization(name="Tenant Beta Corp", slug=f"beta-{uuid.uuid4().hex[:6]}")
        self.site_b = Site(organization_id=self.org_b.id, name="Beta Site", code="BS-1")
        self.plant_b = Plant(organization_id=self.org_b.id, site_id=self.site_b.id, name="Beta Plant", code="BP-1")
        self.line_b = ProductionLine(organization_id=self.org_b.id, plant_id=self.plant_b.id, name="Beta Line", code="BL-1")
        self.asset_b = Asset(organization_id=self.org_b.id, plant_id=self.plant_b.id, name="Beta Lathe", asset_tag="TAG-B", asset_type="MECHANICAL")
        self.machine_b = Machine(organization_id=self.org_b.id, asset_id=self.asset_b.id, name="Beta Machine")
        self.wo_b = WorkOrder(
            organization_id=self.org_b.id,
            site_id=self.site_b.id,
            plant_id=self.plant_b.id,
            work_order_number="WO-BETA-200",
            title="Beta Standard Directive",
        )
        self.run_b = ProductionRun(
            organization_id=self.org_b.id,
            site_id=self.site_b.id,
            plant_id=self.plant_b.id,
            production_line_id=self.line_b.id,
            work_order_id=self.wo_b.id,
            run_number="RUN-BETA-200",
            product_code="STANDARD-B",
            planned_quantity=200.0,
            unit_of_measure="UNITS",
        )
        self.item_b = Item(
            organization_id=self.org_b.id,
            sku="SKU-BETA-COMMODITY",
            name="Commercial Grade Solvent B",
            unit_of_measure="L",
        )
        self.loc_b = InventoryLocation(
            organization_id=self.org_b.id,
            site_id=self.site_b.id,
            code="STORE-B",
            name="Beta Standard Storage",
        )
        self.bal_b = InventoryBalance(
            organization_id=self.org_b.id,
            item_id=self.item_b.id,
            location_id=self.loc_b.id,
            quantity=100.0,
        )

        # Users in Tenant Beta
        self.user_b_admin = User(email=f"admin_b_{uuid.uuid4().hex[:6]}@beta.com", password_hash=hash_password("Pass123!"), full_name="Beta Admin")
        self.user_b_engineer = User(email=f"eng_b_{uuid.uuid4().hex[:6]}@beta.com", password_hash=hash_password("Pass123!"), full_name="Beta Engineer")
        self.user_b_operator = User(email=f"op_b_{uuid.uuid4().hex[:6]}@beta.com", password_hash=hash_password("Pass123!"), full_name="Beta Operator")
        self.user_b_analyst = User(email=f"an_b_{uuid.uuid4().hex[:6]}@beta.com", password_hash=hash_password("Pass123!"), full_name="Beta Analyst")
        self.user_b_viewer = User(email=f"vi_b_{uuid.uuid4().hex[:6]}@beta.com", password_hash=hash_password("Pass123!"), full_name="Beta Viewer")

        async def init():
            # Seed Alpha
            await organization_repo.add(self.org_a)
            await site_repo.add(self.site_a)
            await plant_repo.add(self.plant_a)
            await production_line_repo.add(self.line_a)
            await asset_repo.add(self.asset_a)
            await machine_repo.add(self.machine_a)
            await work_order_repo.add(self.wo_a)
            await production_run_repo.add(self.run_a)
            await maintenance_order_repo.add(self.maint_a)
            await item_repo.add(self.item_a)
            await inventory_location_repo.add(self.loc_a)
            await inventory_balance_repo.add(self.bal_a)

            # Seed Beta
            await organization_repo.add(self.org_b)
            await site_repo.add(self.site_b)
            await plant_repo.add(self.plant_b)
            await production_line_repo.add(self.line_b)
            await asset_repo.add(self.asset_b)
            await machine_repo.add(self.machine_b)
            await work_order_repo.add(self.wo_b)
            await production_run_repo.add(self.run_b)
            await item_repo.add(self.item_b)
            await inventory_location_repo.add(self.loc_b)
            await inventory_balance_repo.add(self.bal_b)

            # Seed Beta Users & Memberships
            for u, r in [
                (self.user_b_admin, "ADMIN"),
                (self.user_b_engineer, "ENGINEER"),
                (self.user_b_operator, "OPERATOR"),
                (self.user_b_analyst, "ANALYST"),
                (self.user_b_viewer, "VIEWER"),
            ]:
                await user_repo.add(u)
                await membership_repo.add(Membership(user_id=u.id, organization_id=self.org_b.id, role=r))

        asyncio.run(init())
        self.token_admin = create_access_token(self.user_b_admin.id, self.user_b_admin.email)
        self.token_engineer = create_access_token(self.user_b_engineer.id, self.user_b_engineer.email)
        self.token_operator = create_access_token(self.user_b_operator.id, self.user_b_operator.email)
        self.token_analyst = create_access_token(self.user_b_analyst.id, self.user_b_analyst.email)
        self.token_viewer = create_access_token(self.user_b_viewer.id, self.user_b_viewer.email)

    # --------------------------------------------------------------------------
    # 1-3. Work Order Cross-Tenant Attacks
    # --------------------------------------------------------------------------

    def test_attack_1_read_org_a_work_order_fails(self):
        res = self.client.get(
            f"/api/v1/work-orders/{self.wo_a.id}",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"]["code"], "RESOURCE_NOT_FOUND")

    def test_attack_2_modify_org_a_work_order_fails(self):
        res = self.client.patch(
            f"/api/v1/work-orders/{self.wo_a.id}",
            json={"title": "Hacked Title"},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_3_release_or_cancel_org_a_work_order_fails(self):
        res1 = self.client.post(
            f"/api/v1/work-orders/{self.wo_a.id}/release",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res1.status_code, 404)

        res2 = self.client.post(
            f"/api/v1/work-orders/{self.wo_a.id}/cancel",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res2.status_code, 404)

    # --------------------------------------------------------------------------
    # 4-5. Production Run Cross-Tenant Attacks
    # --------------------------------------------------------------------------

    def test_attack_4_read_org_a_production_run_fails(self):
        res = self.client.get(
            f"/api/v1/production-runs/{self.run_a.id}",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_5_start_or_abort_org_a_production_run_fails(self):
        res1 = self.client.post(
            f"/api/v1/production-runs/{self.run_a.id}/start",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res1.status_code, 404)

        res2 = self.client.post(
            f"/api/v1/production-runs/{self.run_a.id}/abort",
            json={"reason": "Hacked Abort"},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res2.status_code, 404)

    # --------------------------------------------------------------------------
    # 6-7. Maintenance Order Cross-Tenant Attacks
    # --------------------------------------------------------------------------

    def test_attack_6_read_org_a_maintenance_order_fails(self):
        res = self.client.get(
            f"/api/v1/maintenance/work-orders/{self.maint_a.id}",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_7_start_or_complete_org_a_maintenance_order_fails(self):
        res1 = self.client.post(
            f"/api/v1/maintenance/work-orders/{self.maint_a.id}/start",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res1.status_code, 404)

        res2 = self.client.post(
            f"/api/v1/maintenance/work-orders/{self.maint_a.id}/complete",
            json={"corrective_action": "Hacked Action"},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res2.status_code, 404)

    # --------------------------------------------------------------------------
    # 8-10. Inventory Cross-Tenant Attacks
    # --------------------------------------------------------------------------

    def test_attack_8_read_org_a_item_fails(self):
        res = self.client.get(
            f"/api/v1/items/{self.item_a.id}",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_9_org_b_listing_never_leaks_org_a_items_or_balances(self):
        items_res = self.client.get(
            "/api/v1/items",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(items_res.status_code, 200)
        skus = [i["sku"] for i in items_res.json()]
        self.assertIn("SKU-BETA-COMMODITY", skus)
        self.assertNotIn("SKU-SECRET-A", skus)

        bal_res = self.client.get(
            "/api/v1/inventory/balances",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(bal_res.status_code, 200)
        bal_item_ids = [b["item_id"] for b in bal_res.json()]
        self.assertIn(str(self.item_b.id), bal_item_ids)
        self.assertNotIn(str(self.item_a.id), bal_item_ids)

    def test_attack_10_issue_or_transfer_org_a_inventory_fails(self):
        # Attempt to issue Org A item from Org A location
        res1 = self.client.post(
            "/api/v1/inventory/issues",
            json={"item_id": str(self.item_a.id), "location_id": str(self.loc_a.id), "quantity": 10.0},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res1.status_code, 404)

        # Attempt to transfer from Org A location to Org B location
        res2 = self.client.post(
            "/api/v1/inventory/transfers",
            json={
                "item_id": str(self.item_a.id),
                "source_location_id": str(self.loc_a.id),
                "destination_location_id": str(self.loc_b.id),
                "quantity": 5.0,
            },
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res2.status_code, 404)

    def test_attack_11_consume_org_a_material_in_org_b_run_fails(self):
        # Org B Production Run attempts to consume Org A Item & Location
        res = self.client.post(
            f"/api/v1/production-runs/{self.run_b.id}/materials/consume",
            json={"item_id": str(self.item_a.id), "location_id": str(self.loc_a.id), "quantity": 5.0},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    # --------------------------------------------------------------------------
    # 12-14. Cross-Tenant Foreign Key Injections
    # --------------------------------------------------------------------------

    def test_attack_12_cross_tenant_work_order_creation_fails(self):
        # Org B attempts to create Work Order referencing Plant A from Org A
        res = self.client.post(
            "/api/v1/work-orders",
            json={
                "site_id": str(self.site_b.id),
                "plant_id": str(self.plant_a.id),  # Injected Org A Plant
                "work_order_number": "WO-INJECT-1",
                "title": "Injected Plant WO",
            },
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_13_cross_tenant_production_run_creation_fails(self):
        # Org B attempts to create Production Run referencing Work Order A from Org A
        res = self.client.post(
            "/api/v1/production-runs",
            json={
                "site_id": str(self.site_b.id),
                "plant_id": str(self.plant_b.id),
                "production_line_id": str(self.line_b.id),
                "work_order_id": str(self.wo_a.id),  # Injected Org A Work Order
                "run_number": "RUN-INJECT-1",
                "product_code": "PROD-B",
                "planned_quantity": 50.0,
                "unit_of_measure": "UNITS",
            },
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)
        self.assertIn("Work Order", res.json()["error"]["message"])

    def test_attack_14_cross_tenant_maintenance_creation_fails(self):
        # Org B attempts to create Maintenance referencing Machine A from Org A
        res = self.client.post(
            "/api/v1/maintenance/work-orders",
            json={
                "site_id": str(self.site_b.id),
                "plant_id": str(self.plant_b.id),
                "work_order_number": "WO-MNT-INJ",
                "title": "Injected Machine Maintenance",
                "fault_description": "Cross-tenant attack",
                "machine_id": str(self.machine_a.id),  # Injected Org A Machine
            },
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    # --------------------------------------------------------------------------
    # 15. Header Forgery
    # --------------------------------------------------------------------------

    def test_attack_15_forged_header_to_org_a_rejected(self):
        for endpoint in [
            "/api/v1/work-orders",
            "/api/v1/production-runs",
            "/api/v1/maintenance/work-orders",
            "/api/v1/items",
            "/api/v1/inventory/balances",
        ]:
            res = self.client.get(
                endpoint,
                headers={"Authorization": f"Bearer {self.token_admin}", "X-Organization-ID": str(self.org_a.id)},
            )
            self.assertEqual(res.status_code, 403)
            self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")

    # --------------------------------------------------------------------------
    # 16-18. RBAC Role Violations
    # --------------------------------------------------------------------------

    def test_attack_16_viewer_cannot_mutate_operations_or_inventory(self):
        # Viewer cannot create work order
        res1 = self.client.post(
            "/api/v1/work-orders",
            json={"site_id": str(self.site_b.id), "plant_id": str(self.plant_b.id), "work_order_number": "WO-V", "title": "V WO"},
            headers={"Authorization": f"Bearer {self.token_viewer}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res1.status_code, 403)

        # Viewer cannot create item
        res2 = self.client.post(
            "/api/v1/items",
            json={"sku": "SKU-V", "name": "V Item", "unit_of_measure": "UNITS"},
            headers={"Authorization": f"Bearer {self.token_viewer}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res2.status_code, 403)

    def test_attack_17_analyst_cannot_mutate_operations_or_inventory(self):
        # Analyst cannot create production run
        res = self.client.post(
            "/api/v1/production-runs",
            json={
                "site_id": str(self.site_b.id),
                "plant_id": str(self.plant_b.id),
                "production_line_id": str(self.line_b.id),
                "work_order_id": str(self.wo_b.id),
                "run_number": "RUN-AN",
                "product_code": "PROD-AN",
                "planned_quantity": 10.0,
                "unit_of_measure": "UNITS",
            },
            headers={"Authorization": f"Bearer {self.token_analyst}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
