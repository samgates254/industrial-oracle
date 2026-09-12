"""Integration tests for Telemetry Point associations on Machines."""

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
from industrial_oracle.organization.domain.models import Membership, Organization
from industrial_oracle.organization.infrastructure.repository import (
    membership_repo,
    organization_repo,
)


class TestTelemetryAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.org = Organization(name="Telemetry Org", slug=f"telem-org-{uuid.uuid4().hex[:6]}")
        self.asset = Asset(
            organization_id=self.org.id,
            name="Turbine Asset",
            asset_tag=f"TRB-{uuid.uuid4().hex[:6].upper()}",
            asset_type="MECHANICAL",
        )
        self.machine = Machine(
            organization_id=self.org.id,
            asset_id=self.asset.id,
            name="Gas Turbine 1",
            power_rating_kw=500.0,
        )
        self.engineer = User(
            email=f"telem_eng_{uuid.uuid4().hex[:6]}@example.com",
            password_hash=hash_password("Pass123!"),
            full_name="Telemetry Engineer",
        )
        self.membership = Membership(user_id=self.engineer.id, organization_id=self.org.id, role="ENGINEER")

        async def init():
            await organization_repo.add(self.org)
            await asset_repo.add(self.asset)
            await machine_repo.add(self.machine)
            await user_repo.add(self.engineer)
            await membership_repo.add(self.membership)

        asyncio.run(init())
        self.token = create_access_token(self.engineer.id, self.engineer.email)

    def test_bind_and_list_telemetry_points(self):
        # 1. Bind vibration sensor
        vib_res = self.client.post(
            f"/api/v1/machines/{self.machine.id}/telemetry-points",
            json={
                "metric_name": "bearing_vibration_axial",
                "unit": "mm/s",
                "min_threshold": 0.0,
                "max_threshold": 7.1,
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(vib_res.status_code, 201)
        vib_data = vib_res.json()
        self.assertEqual(vib_data["metric_name"], "bearing_vibration_axial")
        self.assertEqual(vib_data["unit"], "mm/s")

        # 2. Bind temperature sensor
        temp_res = self.client.post(
            f"/api/v1/machines/{self.machine.id}/telemetry-points",
            json={
                "metric_name": "exhaust_gas_temperature",
                "unit": "degC",
                "min_threshold": 200.0,
                "max_threshold": 650.0,
            },
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(temp_res.status_code, 201)

        # 3. List telemetry channels on machine
        list_res = self.client.get(
            f"/api/v1/machines/{self.machine.id}/telemetry-points",
            headers={"Authorization": f"Bearer {self.token}", "X-Organization-ID": str(self.org.id)},
        )
        self.assertEqual(list_res.status_code, 200)
        points = list_res.json()
        self.assertEqual(len(points), 2)
        metric_names = {p["metric_name"] for p in points}
        self.assertIn("bearing_vibration_axial", metric_names)
        self.assertIn("exhaust_gas_temperature", metric_names)


if __name__ == "__main__":
    unittest.main()
