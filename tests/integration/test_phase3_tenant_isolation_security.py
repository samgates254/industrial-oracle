"""Mandatory Phase 3 Cross-Tenant Security and Isolation Tests.

Hard Security Invariant:
A user from Organization B MUST NEVER be able to read, modify, delete,
or otherwise access Assets, Production Lines, Machines, or Telemetry
belonging to Organization A.
"""

import asyncio
import unittest
import uuid
from fastapi.testclient import TestClient

from apps.api.main import app
from industrial_oracle.assets.domain.models import Asset, Machine, ProductionLine, TelemetryPoint
from industrial_oracle.assets.infrastructure.repository import (
    asset_repo,
    machine_repo,
    production_line_repo,
    telemetry_point_repo,
)
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


class TestPhase3TenantIsolationSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # -------------------------------------------------------------
        # Organization Alpha Setup
        # -------------------------------------------------------------
        self.org_a = Organization(name="Tenant Alpha Corp", slug=f"alpha-{uuid.uuid4().hex[:6]}")
        self.user_a = User(
            email=f"admin_a_{uuid.uuid4().hex[:6]}@alpha.com",
            password_hash=hash_password("AlphaPass123!"),
            full_name="Alpha Admin",
        )
        self.membership_a = Membership(user_id=self.user_a.id, organization_id=self.org_a.id, role="ADMIN")
        self.site_a = Site(organization_id=self.org_a.id, name="Alpha Site", code="AS-1")
        self.plant_a = Plant(organization_id=self.org_a.id, site_id=self.site_a.id, name="Alpha Smelter", code="AP-1")
        self.line_a = ProductionLine(
            organization_id=self.org_a.id,
            plant_id=self.plant_a.id,
            name="Alpha Line 1",
            code="ALINE-1",
        )
        self.asset_a = Asset(
            organization_id=self.org_a.id,
            plant_id=self.plant_a.id,
            name="Alpha High-Pressure Press",
            asset_tag="TAG-ALPHA-01",
            asset_type="HYDRAULIC",
        )
        self.machine_a = Machine(
            organization_id=self.org_a.id,
            asset_id=self.asset_a.id,
            production_line_id=self.line_a.id,
            name="Alpha Press Machine",
            power_rating_kw=150.0,
        )
        self.telemetry_a = TelemetryPoint(
            organization_id=self.org_a.id,
            machine_id=self.machine_a.id,
            metric_name="oil_pressure",
            unit="bar",
        )

        # -------------------------------------------------------------
        # Organization Beta Setup
        # -------------------------------------------------------------
        self.org_b = Organization(name="Tenant Beta Corp", slug=f"beta-{uuid.uuid4().hex[:6]}")
        self.user_b = User(
            email=f"admin_b_{uuid.uuid4().hex[:6]}@beta.com",
            password_hash=hash_password("BetaPass123!"),
            full_name="Beta Admin",
        )
        self.membership_b = Membership(user_id=self.user_b.id, organization_id=self.org_b.id, role="ADMIN")
        self.site_b = Site(organization_id=self.org_b.id, name="Beta Site", code="BS-1")
        self.plant_b = Plant(organization_id=self.org_b.id, site_id=self.site_b.id, name="Beta Refinery", code="BP-1")
        self.line_b = ProductionLine(
            organization_id=self.org_b.id,
            plant_id=self.plant_b.id,
            name="Beta Line 1",
            code="BLINE-1",
        )
        self.asset_b = Asset(
            organization_id=self.org_b.id,
            plant_id=self.plant_b.id,
            name="Beta CNC Lathe",
            asset_tag="TAG-BETA-01",
            asset_type="MECHANICAL",
        )
        self.machine_b = Machine(
            organization_id=self.org_b.id,
            asset_id=self.asset_b.id,
            production_line_id=self.line_b.id,
            name="Beta Lathe Machine",
            power_rating_kw=55.0,
        )

        async def init():
            # Seed Alpha
            await organization_repo.add(self.org_a)
            await user_repo.add(self.user_a)
            await membership_repo.add(self.membership_a)
            await site_repo.add(self.site_a)
            await plant_repo.add(self.plant_a)
            await production_line_repo.add(self.line_a)
            await asset_repo.add(self.asset_a)
            await machine_repo.add(self.machine_a)
            await telemetry_point_repo.add(self.telemetry_a)

            # Seed Beta
            await organization_repo.add(self.org_b)
            await user_repo.add(self.user_b)
            await membership_repo.add(self.membership_b)
            await site_repo.add(self.site_b)
            await plant_repo.add(self.plant_b)
            await production_line_repo.add(self.line_b)
            await asset_repo.add(self.asset_b)
            await machine_repo.add(self.machine_b)

        asyncio.run(init())
        self.token_b = create_access_token(self.user_b.id, self.user_b.email)

    def test_attack_user_b_cannot_read_asset_a(self):
        """User B attempts GET /api/v1/assets/{asset_a_id}."""
        res = self.client.get(
            f"/api/v1/assets/{self.asset_a.id}",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["error"]["code"], "RESOURCE_NOT_FOUND")

    def test_attack_user_b_cannot_update_asset_a(self):
        """User B attempts PATCH /api/v1/assets/{asset_a_id}."""
        res = self.client.patch(
            f"/api/v1/assets/{self.asset_a.id}",
            json={"name": "Hacked Asset Name"},
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_user_b_cannot_delete_asset_a(self):
        """User B attempts DELETE /api/v1/assets/{asset_a_id}."""
        res = self.client.delete(
            f"/api/v1/assets/{self.asset_a.id}",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_user_b_cannot_read_line_a(self):
        """User B attempts GET /api/v1/production-lines/{line_a_id}."""
        res = self.client.get(
            f"/api/v1/production-lines/{self.line_a.id}",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_user_b_cannot_read_or_control_machine_a(self):
        """User B attempts GET and POST /start on machine A."""
        get_res = self.client.get(
            f"/api/v1/machines/{self.machine_a.id}",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(get_res.status_code, 404)

        start_res = self.client.post(
            f"/api/v1/machines/{self.machine_a.id}/start",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(start_res.status_code, 404)

        stop_res = self.client.post(
            f"/api/v1/machines/{self.machine_a.id}/stop",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(stop_res.status_code, 404)

    def test_attack_user_b_cannot_bind_telemetry_to_machine_a(self):
        """User B attempts to register a telemetry point on Machine A."""
        res = self.client.post(
            f"/api/v1/machines/{self.machine_a.id}/telemetry-points",
            json={"metric_name": "forged_metric", "unit": "psi"},
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)

    def test_attack_user_b_cannot_link_new_machine_to_asset_a(self):
        """User B attempts to create a machine in Org B linked to Asset A from Org A."""
        payload = {
            "asset_id": str(self.asset_a.id),
            "name": "Trojan Machine",
        }
        res = self.client.post(
            "/api/v1/machines",
            json=payload,
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)
        self.assertIn("Asset", res.json()["error"]["message"])

    def test_attack_user_b_cannot_create_line_in_plant_a(self):
        """User B attempts to create a line in Org B linked to Plant A from Org A."""
        payload = {
            "plant_id": str(self.plant_a.id),
            "name": "Cross-Plant Line",
            "code": "CPL-01",
        }
        res = self.client.post(
            "/api/v1/production-lines",
            json=payload,
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(res.status_code, 404)
        self.assertIn("Plant", res.json()["error"]["message"])

    def test_scoped_queries_never_leak_org_a_assets_or_machines(self):
        """User B query listing assets and machines only returns Org B items."""
        assets_res = self.client.get(
            "/api/v1/assets",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(assets_res.status_code, 200)
        tags = [a["asset_tag"] for a in assets_res.json()]
        self.assertIn("TAG-BETA-01", tags)
        self.assertNotIn("TAG-ALPHA-01", tags)

        machines_res = self.client.get(
            "/api/v1/machines",
            headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_b.id)},
        )
        self.assertEqual(machines_res.status_code, 200)
        m_names = [m["name"] for m in machines_res.json()]
        self.assertIn("Beta Lathe Machine", m_names)
        self.assertNotIn("Alpha Press Machine", m_names)

    def test_header_forgery_to_org_a_rejected(self):
        """User B attempting to forge X-Organization-ID to Org A is rejected with 403."""
        for endpoint in ["/api/v1/assets", "/api/v1/machines", "/api/v1/production-lines"]:
            res = self.client.get(
                endpoint,
                headers={"Authorization": f"Bearer {self.token_b}", "X-Organization-ID": str(self.org_a.id)},
            )
            self.assertEqual(res.status_code, 403)
            self.assertEqual(res.json()["error"]["code"], "FORBIDDEN")


if __name__ == "__main__":
    unittest.main()
