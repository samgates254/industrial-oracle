"""Integration tests for Maintenance Work Orders and Machine State Coordination."""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.assets.domain.models import Asset, Machine
from industrial_oracle.assets.infrastructure.repository import asset_repo, machine_repo
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


class TestMaintenanceAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Maint Test Org", slug=f"maint-org-{uuid.uuid4().hex[:6]}")
        self.site = Site(organization_id=self.org.id, name="Maint Site", code="MS-1")
        self.plant = Plant(organization_id=self.org.id, site_id=self.site.id, name="Maint Plant", code="MP-1")
        self.asset = Asset(
            organization_id=self.org.id,
            plant_id=self.plant.id,
            name="CNC Milling Machine",
            asset_tag=f"CNC-{uuid.uuid4().hex[:6].upper()}",
            asset_type="MECHANICAL",
        )
        self.machine = Machine(
            organization_id=self.org.id,
            asset_id=self.asset.id,
            name="Milling Unit 3",
            power_rating_kw=75.0,
        )

        self.engineer = User(
            email=f"maint_eng_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Maintenance Engineer",
        )
        self.membership = Membership(user_id=self.engineer.id, organization_id=self.org.id, role="ENGINEER")

        async def init():
            await organization_repo.add(self.org)
            await site_repo.add(self.site)
            await plant_repo.add(self.plant)
            await asset_repo.add(self.asset)
            await machine_repo.add(self.machine)
            await user_repo.add(self.engineer)
            await membership_repo.add(self.membership)

        asyncio.run(init())
        self.token = create_access_token(self.engineer.id, self.engineer.email)

    def test_maintenance_order_coordinates_machine_state_lifecycle(self):
        # 1. Create Maintenance Order for Machine
        wo_num = f"WO-MNT-{uuid.uuid4().hex[:6].upper()}"
        payload = {
            "site_id": str(self.site.id),
            "plant_id": str(self.plant.id),
            "work_order_number": wo_num,
            "title": "Spindle Vibration Corrective Maintenance",
            "maintenance_type": "CORRECTIVE",
            "fault_description": "Excessive high-frequency spindle vibration",
            "machine_id": str(self.machine.id),
            "asset_id": str(self.asset.id),
            "priority": "CRITICAL",
            "failure_code": "VIB-SPINDLE-HIGH",
        }
        res = self.client.post(
            "/api/v1/maintenance/work-orders",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(res.status_code, 201)
        maint_data = res.json()
        maint_id = maint_data["id"]
        self.assertEqual(maint_data["status"], "PLANNED")

        # Machine is initially STOPPED
        mach_res = self.client.get(
            f"/api/v1/machines/{self.machine.id}",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(mach_res.json()["status"], "STOPPED")

        # 2. Start Maintenance -> Coordinated Machine state transition to MAINTENANCE
        start_res = self.client.post(
            f"/api/v1/maintenance/work-orders/{maint_id}/start",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(start_res.status_code, 200)
        self.assertEqual(start_res.json()["status"], "IN_PROGRESS")

        # Verify Machine is now in MAINTENANCE state
        mach_after_start = self.client.get(
            f"/api/v1/machines/{self.machine.id}",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(mach_after_start.json()["status"], "MAINTENANCE")

        # 3. Complete Maintenance -> Coordinated Machine state restored to STOPPED
        comp_res = self.client.post(
            f"/api/v1/maintenance/work-orders/{maint_id}/complete",
            json={
                "corrective_action": "Replaced spindle ceramic bearings and balanced rotor",
                "root_cause": "Bearing raceway spalling",
                "downtime_minutes": 120.0,
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(comp_res.status_code, 200)
        self.assertEqual(comp_res.json()["status"], "COMPLETED")
        self.assertEqual(comp_res.json()["downtime_minutes"], 120.0)

        # Verify Machine is restored to STOPPED
        mach_after_comp = self.client.get(
            f"/api/v1/machines/{self.machine.id}",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(mach_after_comp.json()["status"], "STOPPED")


if __name__ == "__main__":
    unittest.main()
